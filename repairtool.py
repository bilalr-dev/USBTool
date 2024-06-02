import tkinter as tk
from tkinter import messagebox
import psutil
import win32api
import subprocess
import re
import ctypes
import sys
import os

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    if is_admin():
        print("Already running with admin privileges.")
    else:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)

if not is_admin():
    run_as_admin()
    sys.exit(0)

def get_usb_sticks():
    usb_info = []
    drives = [f"{d}:\\" for d in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ']
    for drive in drives:
        try:
            partitions = psutil.disk_partitions(all=True)
            for partition in partitions:
                if partition.mountpoint == drive and 'removable' in partition.opts:
                    label = get_drive_label(partition.device)
                    size_gb = get_drive_size(drive)
                    fs_type = get_file_system_type(drive)
                    usb_info.append((drive, label, size_gb, fs_type))
        except Exception as e:
            print(f"Error getting drive type: {e}")
    return usb_info

def get_drive_label(drive):
    try:
        return win32api.GetVolumeInformation(drive)[0]
    except Exception as e:
        print(f"Error getting volume label: {e}")
        return "Unknown"

def get_drive_size(drive):
    try:
        usage = psutil.disk_usage(drive)
        size_gb = round(usage.total / (1024 * 1024 * 1024), 2)
        return size_gb
    except Exception as e:
        print(f"Error getting drive size: {e}")
        return "Unknown"

def get_file_system_type(drive):
    try:
        return win32api.GetVolumeInformation(drive)[4]
    except Exception as e:
        print(f"Error getting file system type: {e}")
        return "Unknown"

def refresh_usb_list():
    usb_sticks = get_usb_sticks()
    listbox.delete(0, tk.END)
    if usb_sticks:
        for drive, label, size_gb, fs_type in usb_sticks:
            usb_info = f"{drive} ({label} - Size: {size_gb} GB - File System: {fs_type})"
            listbox.insert(tk.END, usb_info)
    else:
        messagebox.showinfo("No USB Sticks", "No USB sticks connected.")
    update_format_button_state()

def format_drive():
    selected_drive = listbox.get(tk.ACTIVE)
    if selected_drive:
        drive_letter = selected_drive.split()[0]
        
        def on_format():
            file_system = fs_var.get()
            if file_system in ["FAT32", "NTFS"]:
                answer = messagebox.askyesno("Confirm Format", f"Are you sure you want to format the drive {drive_letter} as {file_system}?")
                if answer:
                    try:
                        process = subprocess.Popen(['diskpart'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                        process.stdin.write(f"select volume {drive_letter.split(':')[0]}\n")
                        process.stdin.write(f"format fs={file_system} quick\n")
                        process.stdin.write("exit\n")
                        process.stdin.flush()
                        
                        # Read the output to get progress
                        progress = ""
                        while True:
                            output = process.stdout.readline()
                            if output == '' and process.poll() is not None:
                                break
                            if output:
                                progress_match = re.match(r'Percentage completed:\s*(\d+)%', output.strip())
                                if progress_match:
                                    progress = progress_match.group(1)
                                    print(f"Formatting progress: {progress}%")
                                    # Update the progress to the user (you can use a progress bar or a label)
                        process.wait()

                        messagebox.showinfo("Format Drive", f"Drive {drive_letter} formatted successfully as {file_system}.")
                        format_window.destroy()
                    except Exception as e:
                        messagebox.showerror("Error", f"Error formatting drive: {e}")
            else:
                messagebox.showwarning("Invalid Input", "Please select a valid file system type.")
        
        format_window = tk.Toplevel(root)
        format_window.title("USB Stick Repair Tool")
        format_window.geometry("300x150")
        format_window.resizable(False, False)
        format_window.iconbitmap(icon_path)
        
        # Get the screen width and height
        screen_width = format_window.winfo_screenwidth()
        screen_height = format_window.winfo_screenheight()

        # Calculate the x and y coordinates to center the window
        x = (screen_width - 300) // 2  # 300 is the width of the window
        y = (screen_height - 150) // 2  # 150 is the height of the window

        # Set the window geometry
        format_window.geometry(f"300x150+{x}+{y}")
        
        fs_var = tk.StringVar(value="FAT32")  # Default value
        fs_choices = ["FAT32", "NTFS"]
        
        label = tk.Label(format_window, text="Select File System:", font=("Arial", 12))
        label.pack(pady=5)
        
        fs_dropdown = tk.OptionMenu(format_window, fs_var, *fs_choices)
        fs_dropdown.config(font=("Arial", 10))
        fs_dropdown.pack(pady=5)
        
        format_button = tk.Button(format_window, text="Format", command=on_format, font=("Arial", 12), bg="#4CAF50", fg="white")
        format_button.pack(pady=10)
    else:
        messagebox.showwarning("Select Drive", "Please select a drive to format.")

def update_format_button_state(event=None):
    selection = listbox.curselection()
    if selection:
        format_button.config(state=tk.NORMAL)
    else:
        format_button.config(state=tk.DISABLED)

# Set up the GUI
root = tk.Tk()
root.title("USB Stick Repair Tool")

# Set custom icon
icon_path = os.path.join(sys._MEIPASS, "favicon.ico") if getattr(sys, "frozen", False) else "favicon.ico"
root.iconbitmap(icon_path)

# Get the screen width and height
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Calculate the x and y coordinates to center the window
x = (screen_width - 600) // 2  # 600 is the width of the window
y = (screen_height - 400) // 2  # 400 is the height of the window

# Set the window geometry
root.geometry(f"600x400+{x}+{y}")

# Prevent resizing of the window
root.resizable(False, False)

background_color = "#F0F0F0"
foreground_color = "#333333"
button_bg_color = "#4CAF50"
button_fg_color = "white"

root.config(bg=background_color)

frame = tk.Frame(root, bg=background_color)
frame.pack(pady=10)

label = tk.Label(frame, text="Connected USB Sticks:", font=("Arial", 14), bg=background_color, fg=foreground_color)
label.pack()

listbox = tk.Listbox(frame, width=60, font=("Arial", 12))
listbox.pack(pady=10)
listbox.bind('<<ListboxSelect>>', update_format_button_state)

button_frame = tk.Frame(frame, bg=background_color)
button_frame.pack(pady=5)

refresh_button = tk.Button(button_frame, text="Refresh", command=refresh_usb_list, font=("Arial", 12), bg=button_bg_color, fg=button_fg_color)
refresh_button.pack(side=tk.LEFT, padx=5)

format_button = tk.Button(button_frame, text="Format", command=format_drive, state=tk.DISABLED, font=("Arial", 12), bg=button_bg_color, fg=button_fg_color)
format_button.pack(side=tk.LEFT, padx=5)

# Copyright label
copyright_label = tk.Label(root, text="©2024. Developed by Bilal Rahaoui", font=("Arial", 10), bg=background_color, fg=foreground_color)
copyright_label.pack(side=tk.BOTTOM, pady=10)

# Initial load of USB sticks
refresh_usb_list()

root.mainloop()
