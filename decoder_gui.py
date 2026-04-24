import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from stego_utils import extract_data


# Extract & decrypt AES-128 watermark from image LSB
def open_image_and_decrypt():
    filepath = filedialog.askopenfilename(
        title="Select Storyboard Image",
        filetypes=[
            ("PNG Files", "*.png"),
            ("All Image Files", "*.png *.jpg *.jpeg *.bmp"),
            ("All Files", "*.*")
        ]
    )
    
    if not filepath:
        return
    
    try:
        status_label.config(text="Extracting data...", fg="blue")
        root.update()
        
        decrypted_text = extract_data(filepath)
        
        if "Failed" in decrypted_text:
            status_label.config(text="No valid watermark found", fg="red")
            messagebox.showerror(
                "Decryption Failed", 
                "No valid watermark found or key mismatch.\n\n"
                "Possible reasons:\n"
                "- Image doesn't contain a watermark\n"
                "- Image was modified (compressed/resized)\n"
                "- Wrong encryption key"
            )
        else:
            status_label.config(text="Watermark extracted successfully!", fg="green")
            result_window = tk.Toplevel(root)
            result_window.title("Extracted Watermark Data")
            result_window.geometry("500x300")
            result_window.transient(root)
            
            header = tk.Label(
                result_window, 
                text="🔒 ENTERPRISE ASSET TRACKING", 
                font=("Helvetica", 14, "bold"),
                fg="green"
            )
            header.pack(pady=10)
            
            text_area = scrolledtext.ScrolledText(
                result_window, 
                wrap=tk.WORD, 
                width=50, 
                height=10,
                font=("Courier", 11)
            )
            text_area.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
            text_area.insert(tk.END, decrypted_text)
            text_area.config(state=tk.DISABLED)
            
            close_btn = tk.Button(
                result_window, 
                text="Close", 
                command=result_window.destroy,
                bg="black",
                fg="white",
                font=("Helvetica", 10),
                width=15
            )
            close_btn.pack(pady=10)
            
    except Exception as e:
        status_label.config(text=f"Error: {str(e)[:50]}", fg="red")
        messagebox.showerror("Error", f"Extraction failed:\n{str(e)}")


def create_gradient_bg(canvas, color1, color2):
    (r1, g1, b1) = canvas.winfo_rgb(color1)
    (r2, g2, b2) = canvas.winfo_rgb(color2)
    
    r_ratio = float(r2 - r1) / 400
    g_ratio = float(g2 - g1) / 400
    b_ratio = float(b2 - b1) / 400
    
    for i in range(400):
        nr = int(r1 + (r_ratio * i))
        ng = int(g1 + (g_ratio * i))
        nb = int(b1 + (b_ratio * i))
        
        color = f"#{nr:04x}{ng:04x}{nb:04x}"
        canvas.create_line(0, i, 500, i, fill=color)


# Tkinter GUI for watermark extraction tool
root = tk.Tk()
root.title("Enterprise Deal Tracker - Decoder")
root.geometry("500x350")
root.resizable(False, False)

root.eval('tk::PlaceWindow . center')

main_frame = tk.Frame(root, padx=30, pady=30)
main_frame.pack(fill=tk.BOTH, expand=True)

label = tk.Label(
    main_frame, 
    text="🔒 PITCH VISUALIZER", 
    font=("Helvetica", 18, "bold")
)
label.pack(pady=5)

subtitle = tk.Label(
    main_frame, 
    text="Enterprise SecOps Tool - Phase E", 
    font=("Helvetica", 12),
    fg="gray"
)
subtitle.pack(pady=5)

separator = tk.Frame(main_frame, height=2, bg="gray", bd=1, relief=tk.SUNKEN)
separator.pack(fill=tk.X, pady=15)

desc_text = tk.Label(
    main_frame,
    text="This tool extracts AES-128 encrypted watermarks\n"
         "embedded in storyboard images using LSB steganography.",
    font=("Helvetica", 10),
    justify=tk.CENTER
)
desc_text.pack(pady=10)

btn = tk.Button(
    main_frame, 
    text="📁 SELECT IMAGE TO DECRYPT", 
    command=open_image_and_decrypt,
    bg="#1a1a2e",
    fg="white",
    font=("Helvetica", 12, "bold"),
    width=30,
    height=2,
    cursor="hand2"
)
btn.pack(pady=20)

status_label = tk.Label(
    main_frame,
    text="Ready",
    font=("Helvetica", 10, "italic"),
    fg="gray"
)
status_label.pack(pady=10)

footer = tk.Label(
    main_frame,
    text="AES-128 Encryption • LSB Steganography • Cryptographic Watermarking",
    font=("Helvetica", 8),
    fg="gray"
)
footer.pack(side=tk.BOTTOM, pady=10)

if __name__ == "__main__":
    root.mainloop()
