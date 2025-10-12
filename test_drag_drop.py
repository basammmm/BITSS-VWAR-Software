"""
Quick test to verify tkinterdnd2 is working
"""
import sys
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    import tkinter as tk
    
    print("Creating test window...")
    root = TkinterDnD.Tk()
    root.title("Drag & Drop Test")
    root.geometry("400x300")
    
    label = tk.Label(root, text="Drag files here\n(If this works, tkinterdnd2 is OK)", 
                     bg="lightgreen", fg="black", font=("Arial", 14), 
                     relief="ridge", bd=3)
    label.pack(fill="both", expand=True, padx=20, pady=20)
    
    def on_drop(event):
        print(f"✅ Drop detected! Data: {event.data}")
        label.config(text=f"✅ SUCCESS!\n\nDropped: {event.data}", bg="lime")
    
    def on_enter(event):
        print("Drag entered")
        label.config(bg="yellow")
    
    def on_leave(event):
        print("Drag left")
        label.config(bg="lightgreen")
    
    try:
        label.drop_target_register(DND_FILES)
        label.dnd_bind('<<Drop>>', on_drop)
        label.dnd_bind('<<DragEnter>>', on_enter)
        label.dnd_bind('<<DragLeave>>', on_leave)
        print("✅ DND registered successfully!")
        print("\nInstructions:")
        print("1. Drag a file from File Explorer")
        print("2. Drop it on the green area")
        print("3. Watch for color changes and messages")
    except Exception as e:
        print(f"❌ DND registration failed: {e}")
        label.config(text=f"❌ DND Failed:\n{e}", bg="red", fg="white")
    
    print("\n💡 Tips:")
    print("- File Explorer must NOT be running as admin")
    print("- This test should NOT be running as admin")
    print("- Both must have same privilege level")
    
    root.mainloop()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
