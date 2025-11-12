#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 11 19:57:16 2025

@author: aravkekane
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import sqlite3
from datetime import datetime, timedelta
import json
import csv
from geopy.geocoders import Nominatim

API_KEY = "YOUR_API_KEY"

DB_name = "weather_data.db"

def setup_database():
    conn = sqlite3.connect(DB_name)
    c = conn.cursor()
    
    c.execute('''Create Table If NOT EXISTS searches
              (id Integer PRIMARY KEY AUTOINCREMENT,
               location TEXT,
               lat REAL,
               lon REAL,
               start_date TEXT,
               end_date TEXT,
               temp REAL,
               feels_like REAL,
               humidity INTEGER,
               weather_desc TEXT,
               wind_speed REAL, 
               timestamp TEXT)''')
    conn.commit()
    conn.close()
    
def save_to_db(location, lat, lon, start, end, temp, feels, humidity, desc, wind):
    conn = sqlite3.connect(DB_name)
    c = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('''INSERT INTO searches (location, lat, lon, start_date, end_date,
                 temp, feels_like, humidity, weather_desc, wind_speed, timestamp)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (location, lat, lon, start, end, temp, feels, humidity, desc, wind, now))
    conn.commit()
    conn.close()
    return c.lastrowid

def get_all_searches():
    conn = sqlite3.connect(DB_name)
    c = conn.cursor()
    
    c.execute('SELECT * FROM searches ORDER BY timestamp DESC')
    rows = c.fetchall()
    
    conn.close()
    return rows

def update_search(search_id, location, start, end):
    conn = sqlite3.connect(DB_name)
    c = conn.cursor()
    
    c.execute('''UPDATE searches SET location=?, start_date=?, end_date=?
                 WHERE id=?''', (location, start, end, search_id))
    
    conn.commit()
    conn.close()

def delete_search(search_id):
    conn = sqlite3.connect(DB_name)
    c = conn.cursor()
    
    c.execute('DELETE FROM searches WHERE id=?', (search_id,))
    
    conn.commit()
    conn.close()
    
def check_location(location_text):
    try:
        if ',' in location_text:
            parts = location_text.split(',')
            lat = float(parts[0].strip())
            lon = float(parts[1].strip())
            
            geolocator = Nominatim(user_agent = "weatherapp")
            place = geolocator.reverse(f"{lat}, {lon}", timeout=10)
            
            if place:
                return True, lat, lon, place.address
            else: 
                return True, lat, lon, location_text
            
        geolocator = Nominatim(user_agent="weatherapp")
        place = geolocator.geocode(location_text, timeout=10)
        
        if place:
            return True, place.latitude, place.longitude, place.address
        else: 
            return False, None, None, "Location Not Found"
        
    except Exception as e :
        return False, None, None, str(e)

def check_dates(start, end):
    try:
        start_date = datetime.strptime(start, '%Y-%m-%d')
        end_date = datetime.strptime(end, '%Y-%m-%d')
        today = datetime.now()
        
        if start_date > end_date:
            return False, "Start date cannot be after the end date"
        
        if start_date < today - timedelta(days=365):
            return False, "Start date is too far in the past"
        
        if end_date > today + timedelta(days=7):
            return False, "End date too far into the future, maximum of 7 days"
        
        if (end_date - start_date).days > 30:
            return False, "Date range too long, maximum of 30 days"
        
        return True, "Ok"
    
    except:
        return False, "Invalid date format"
    
def get_weather(lat, lon):
    if API_KEY == "YOUR_API_KEY_HERE" :
        return None, "Please Add Your API KEY First!!"
    
    url = "https://api.openweathermap.org/data/2.5/weather"
    
    try:
        response = requests.get(url, params={
            'lat': lat,
            'lon': lon,
            'appid': API_KEY,
            'units': 'metric'
        }, timeout=10)
        
        data = response.json()
        
        weather = {
            'temp': data['main']['temp'],
            'feels_like': data['main']['feels_like'],
            'humidity': data['main']['humidity'],
            'description': data['weather'][0]['description'],
            'wind': data['wind']['speed'],
            'pressure': data['main']['pressure']
        }
        
        return weather, None
    
    except Exception as e:
        return None, f"Error: {str(e)}"

def get_forecast(lat, lon):
    if API_KEY == "YOUR_API_KEY_HERE":
        return None, "Please Add Your API KEY First!!"
    
    url = "https://api.openweathermap.org/data/2.5/forecast"
    
    try:
        response = requests.get(url, params={
            'lat': lat,
            'lon': lon,
            'appid': API_KEY,
            'units': 'metric'
        }, timeout=10)
        
        data = response.json()
        
        days = {}
        for item in data['list']:
            date = item['dt_txt'].split(' ')[0]
            if date not in days:
                days[date] = {'temps': [], 'desc': []}
            
            days[date]['temps'].append(item['main']['temp'])
            days[date]['desc'].append(item['weather'][0]['description'])
        
        forecast = []
        for date in list(days.keys())[:5]:
            forecast.append({
                'date': date,
                'high': max(days[date]['temps']),
                'low': min(days[date]['temps']),
                'desc': max(set(days[date]['desc']), key=days[date]['desc'].count)
            })
        
        return forecast, None
        
    except Exception as e:
        return None, f"Error: {str(e)}"

def export_json(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def export_csv(data, filename):
    if not data:
        return
    
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Location', 'Start Date', 'End Date', 'Temperature', 
                        'Humidity', 'Description', 'Timestamp'])
        for row in data:
            writer.writerow(row)

def export_xml(data, filename):
    xml = '<?xml version="1.0"?>\n<searches>\n'
    
    for row in data:
        xml += '  <search>\n'
        xml += f'    <id>{row[0]}</id>\n'
        xml += f'    <location>{row[1]}</location>\n'
        xml += f'    <start_date>{row[4]}</start_date>\n'
        xml += f'    <end_date>{row[5]}</end_date>\n'
        xml += f'    <temperature>{row[6]}</temperature>\n'
        xml += f'    <humidity>{row[8]}</humidity>\n'
        xml += f'    <description>{row[9]}</description>\n'
        xml += f'    <timestamp>{row[11]}</timestamp>\n'
        xml += '  </search>\n'
    
    xml += '</searches>'
    
    with open(filename, 'w') as f:
        f.write(xml)

def export_markdown(data, filename):
    md = '# Weather Search History\n\n'
    
    for row in data:
        md += f'## Search #{row[0]}\n\n'
        md += f'**Location:** {row[1]}\n\n'
        md += f'**Date Range:** {row[4]} to {row[5]}\n\n'
        md += f'**Temperature:** {row[6]}°C\n\n'
        md += f'**Humidity:** {row[8]}%\n\n'
        md += f'**Weather:** {row[9]}\n\n'
        md += f'**Saved:** {row[11]}\n\n'
        md += '---\n\n'
    
    with open(filename, 'w') as f:
        f.write(md)

class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Weather App")
        self.root.geometry("1000x700")
        
        setup_database()
        
        self.setup_gui()
        
        self.refresh_table()
    
    def setup_gui(self):
        header = tk.Frame(self.root, bg='#4a90e2', height = 80)
        header.pack(fill='x')
        
        tk.Label(header, text="Weather App", font=('Arial', 20, 'bold'),
                bg='#4a90e2', fg='white').pack(pady=10)
        
        tk.Label(header, text="by Arav", font=('Arial', 10),
                bg='#4a90e2', fg='white').pack()
        
        search_frame = tk.LabelFrame(self.root, text="Search Weather", 
                                     font=('Arial', 12, 'bold'), padx=10, pady=10)
        search_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(search_frame, text="Location:").grid(row=0, column=0, sticky='w', pady=5)
        self.location_input = tk.Entry(search_frame, width=40)
        self.location_input.grid(row=0, column=1, pady=5, padx=5)
        self.location_input.insert(0, "New York")
        
        tk.Label(search_frame, text="(City, Zip, or Coordinates)", 
                fg='gray', font=('Arial', 8)).grid(row=1, column=1, sticky='w')
        
        tk.Label(search_frame, text="Start Date:").grid(row=2, column=0, sticky='w', pady=5)
        self.start_input = tk.Entry(search_frame, width=20)
        self.start_input.grid(row=2, column=1, sticky='w', pady=5, padx=5)
        self.start_input.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        tk.Label(search_frame, text="End Date:").grid(row=3, column=0, sticky='w', pady=5)
        self.end_input = tk.Entry(search_frame, width=20)
        self.end_input.grid(row=3, column=1, sticky='w', pady=5, padx=5)
        self.end_input.insert(0, (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'))
        
        tk.Button(search_frame, text="Search", bg='#4a90e2', fg='white',
                 font=('Arial', 11, 'bold'), command=self.do_search,
                 padx=20, pady=5).grid(row=4, column=1, sticky='w', pady=10, padx=5)
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.current_tab = tk.Frame(self.notebook)
        self.notebook.add(self.current_tab, text='Current Weather')
        
        self.current_display = tk.Text(self.current_tab, font=('Courier', 10), 
                                       wrap='word', height=12)
        self.current_display.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.forecast_tab = tk.Frame(self.notebook)
        self.notebook.add(self.forecast_tab, text='5-Day Forecast')
        
        self.forecast_display = tk.Text(self.forecast_tab, font=('Courier', 10),
                                        wrap='word', height=12)
        self.forecast_display.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.db_tab = tk.Frame(self.notebook)
        self.notebook.add(self.db_tab, text='Saved Searches')
        
        btn_frame = tk.Frame(self.db_tab)
        btn_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Button(btn_frame, text="Refresh", command=self.refresh_table,
                 bg='#28a745', fg='white').pack(side='left', padx=2)
        
        tk.Button(btn_frame, text="Edit", command=self.edit_selected,
                 bg='#ffc107').pack(side='left', padx=2)
        
        tk.Button(btn_frame, text="Delete", command=self.delete_selected,
                 bg='#dc3545', fg='white').pack(side='left', padx=2)
        
        tk.Label(btn_frame, text=" | Export: ").pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="JSON", command=lambda: self.do_export('json'),
                 bg='#17a2b8', fg='white').pack(side='left', padx=2)
        
        tk.Button(btn_frame, text="CSV", command=lambda: self.do_export('csv'),
                 bg='#17a2b8', fg='white').pack(side='left', padx=2)
        
        tk.Button(btn_frame, text="XML", command=lambda: self.do_export('xml'),
                 bg='#17a2b8', fg='white').pack(side='left', padx=2)
        
        tk.Button(btn_frame, text="MD", command=lambda: self.do_export('md'),
                 bg='#17a2b8', fg='white').pack(side='left', padx=2)
        
        table_frame = tk.Frame(self.db_tab)
        table_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        scroll = tk.Scrollbar(table_frame)
        scroll.pack(side='right', fill='y')
        
        self.table = ttk.Treeview(table_frame, yscrollcommand=scroll.set,
                                  columns=('ID', 'Location', 'Dates', 'Temp', 'Weather', 'Time'),
                                  show='headings')
        
        self.table.heading('ID', text='ID')
        self.table.heading('Location', text='Location')
        self.table.heading('Dates', text='Date Range')
        self.table.heading('Temp', text='Temp (°C)')
        self.table.heading('Weather', text='Weather')
        self.table.heading('Time', text='Saved At')
        
        self.table.column('ID', width=40)
        self.table.column('Location', width=150)
        self.table.column('Dates', width=120)
        self.table.column('Temp', width=70)
        self.table.column('Weather', width=120)
        self.table.column('Time', width=140)
        
        self.table.pack(side='left', fill='both', expand=True)
        scroll.config(command=self.table.yview)
        
        tk.Button(self.root, text="About PM Accelerator", 
                 command=self.show_about,
                 bg='#6c757d', fg='white').pack(pady=5)
    
    def do_search(self):
        location = self.location_input.get().strip()
        start = self.start_input.get().strip()
        end = self.end_input.get().strip()
        
        if not location:
            messagebox.showerror("Error", "Please Enter a Location")
            return
        
        if not end:
            end = start
            
        dates_ok, date_msg = check_dates(start, end)
        if not dates_ok:
            messagebox.showerror("Error", date_msg)
            return
        
        self.current_display.delete('1.0', tk.END)
        self.current_display.insert('1.0', "Searching...\n")
        self.root.update()
        
        loc_ok, lat, lon, place_name = check_location(location)
        
        if not loc_ok:
            self.current_display.delete('1.0', tk.END)
            self.current_display.insert('1.0', f"Error: {place_name}\n")
            return
        
        self.current_display.insert(tk.END, "Getting weather data...\n")
        self.root.update()
        
        weather, error = get_weather(lat, lon)
        
        if error:
            self.current_display.delete('1.0', tk.END)
            self.current_display.insert('1.0', f"Error: {error}\n")
            return
        
        text = f"""
CURRENT WEATHER
{'='*50}

Location: {place_name}
Coordinates: {lat:.4f}, {lon:.4f}

Temperature: {weather['temp']}°C
Feels Like: {weather['feels_like']}°C
Weather: {weather['description']}
Humidity: {weather['humidity']}%
Wind Speed: {weather['wind']} m/s
Pressure: {weather['pressure']} hPa

Date Range: {start} to {end}
"""
        self.current_display.insert('1.0', text)
        
        forecast, error = get_forecast(lat, lon)
        
        if not error:
            self.forecast_display.delete('1.0', tk.END)
            text = "\n5-DAY FORECAST\n" + "="*50 + "\n\n"
            
            for day in forecast:
                text += f"Date: {day['date']}\n"
                text += f"  High: {day['high']:.1f}°C | Low: {day['low']:.1f}°C\n"
                text += f"  {day['desc']}\n\n"
            
            self.forecast_display.insert('1.0', text)
        
        try:
            save_to_db(place_name, lat, lon, start, end, 
                      weather['temp'], weather['feels_like'], weather['humidity'],
                      weather['description'], weather['wind'])
            
            self.current_display.insert(tk.END, "\nSaved to database!\n")
            self.refresh_table()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {str(e)}")
    
    def refresh_table(self):
        for item in self.table.get_children():
            self.table.delete(item)
        
        rows = get_all_searches()
        
        for row in rows:
            self.table.insert('', 'end', values=(
                row[0],  
                row[1][:25],  
                f"{row[4]} to {row[5]}",  
                f"{row[6]}",  
                row[9],  
                row[11]  
            ))
    
    def edit_selected(self):
        selected = self.table.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a record to edit")
            return
        
        item = self.table.item(selected[0])
        values = item['values']
        search_id = values[0]
        location = values[1]
        dates = values[2].split(' to ')
        
        edit_win = tk.Toplevel(self.root)
        edit_win.title("Edit Search")
        edit_win.geometry("350x200")
        
        tk.Label(edit_win, text="Edit Search Record", 
                font=('Arial', 12, 'bold')).pack(pady=10)
        
        tk.Label(edit_win, text="Location:").pack()
        loc_entry = tk.Entry(edit_win, width=40)
        loc_entry.insert(0, location)
        loc_entry.pack(pady=2)
        
        tk.Label(edit_win, text="Start Date:").pack()
        start_entry = tk.Entry(edit_win, width=40)
        start_entry.insert(0, dates[0])
        start_entry.pack(pady=2)
        
        tk.Label(edit_win, text="End Date:").pack()
        end_entry = tk.Entry(edit_win, width=40)
        end_entry.insert(0, dates[1])
        end_entry.pack(pady=2)
        
        def save_edit():
            new_loc = loc_entry.get()
            new_start = start_entry.get()
            new_end = end_entry.get()
            
            if not all([new_loc, new_start, new_end]):
                messagebox.showerror("Error", "All fields required!")
                return
            
            dates_ok, msg = check_dates(new_start, new_end)
            if not dates_ok:
                messagebox.showerror("Error", msg)
                return
            
            update_search(search_id, new_loc, new_start, new_end)
            messagebox.showinfo("Success", "Record updated!")
            edit_win.destroy()
            self.refresh_table()
        
        tk.Button(edit_win, text="Save Changes", command=save_edit,
                 bg='#28a745', fg='white', font=('Arial', 10, 'bold')).pack(pady=10)
    
    def delete_selected(self):
        selected = self.table.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a record to delete")
            return
        
        item = self.table.item(selected[0])
        search_id = item['values'][0]
        location = item['values'][1]
        
        if messagebox.askyesno("Confirm", f"Delete search for '{location}'?"):
            delete_search(search_id)
            messagebox.showinfo("Success", "Record deleted!")
            self.refresh_table()
    
    def do_export(self, format_type):
        data = get_all_searches()
        
        if not data:
            messagebox.showwarning("Warning", "No data to export")
            return
        
        filetypes = {
            'json': [('JSON files', '*.json')],
            'csv': [('CSV files', '*.csv')],
            'xml': [('XML files', '*.xml')],
            'md': [('Markdown files', '*.md')]
        }
        
        filename = filedialog.asksaveasfilename(
            defaultextension=f'.{format_type}',
            filetypes=filetypes[format_type]
        )
        
        if not filename:
            return
        
        try:
            if format_type == 'json':
                json_data = []
                for row in data:
                    json_data.append({
                        'id': row[0], 'location': row[1], 'lat': row[2], 'lon': row[3],
                        'start_date': row[4], 'end_date': row[5], 'temp': row[6],
                        'feels_like': row[7], 'humidity': row[8], 'description': row[9],
                        'wind_speed': row[10], 'timestamp': row[11]
                    })
                export_json(json_data, filename)
            
            elif format_type == 'csv':
                export_csv(data, filename)
            
            elif format_type == 'xml':
                export_xml(data, filename)
            
            elif format_type == 'md':
                export_markdown(data, filename)
            
            messagebox.showinfo("Success", f"Exported to:\n{filename}")
        
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {str(e)}")
    
    def show_about(self):
        about_win = tk.Toplevel(self.root)
        about_win.title("About PM Accelerator")
        about_win.geometry("500x400")
        
        text = tk.Text(about_win, wrap='word', font=('Arial', 10))
        text.pack(fill='both', expand=True, padx=10, pady=10)
        
        info = """
About Product Manager Accelerator

The Product Manager Accelerator Program is designed to support PM 
professionals through every stage of their career. From students 
looking for entry-level jobs to Directors looking to take on a 
leadership role, our program has helped hundreds of students 
fulfill their career aspirations.

Our Product Manager Accelerator community is ambitious and committed. 
Through our program, they have learned, honed, and developed new PM 
and leadership skills, giving them a strong foundation for their 
future endeavors.

Learn more at:
LinkedIn: linkedin.com/company/productmanageraccelerator
"""
        text.insert('1.0', info)
        text.config(state='disabled')

if __name__ == '__main__':
    root = tk.Tk()
    app = WeatherApp(root)
    root.mainloop()
    
    
    
