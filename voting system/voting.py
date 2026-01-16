import tkinter as tk
from tkinter import messagebox, ttk
import random
import smtplib
import ssl
import sqlite3
from email.message import EmailMessage

class CompetitionVotingSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Online Voting System - Competition Version")
        self.root.geometry("1100x650")
        self.root.configure(bg="#f0f2f5")

        # ===== CONFIGURATION (Updated from your screenshots) =====
        self.SENDER_EMAIL = "ashith232@gmail.com"  # Your email
        self.APP_PASSWORD = "kmym ucuk iyux kpxr"   # Your app password
        # ========================================================

        self.current_otp = ""
        self.init_db()
        self.setup_styles()
        self.create_main_layout()
        self.root.withdraw()   # 👈 ADD THIS LINE
        
        # Start with the verification gate
        self.show_verification_overlay()

    def enable_voting(self):
        for btn in self.vote_buttons:
            btn.config(state="normal")


    def init_db(self):
        self.conn = sqlite3.connect("voting_data.db")
        self.cursor = self.conn.cursor()

        self.cursor.execute(
            'CREATE TABLE IF NOT EXISTS voters (name TEXT PRIMARY KEY, has_voted INTEGER DEFAULT 0)'
        )
        self.cursor.execute(
            'CREATE TABLE IF NOT EXISTS results (candidate TEXT PRIMARY KEY, count INTEGER DEFAULT 0)'
        )

    # ✅ CLEAR ALL REGISTRATIONS ON REFRESH
        self.cursor.execute("DELETE FROM voters")

    # ✅ RESET RESULTS
        self.cursor.execute("DELETE FROM results")
        for cand in ["A", "B", "C"]:
            self.cursor.execute("INSERT INTO results VALUES (?, 0)", (cand,))

        self.conn.commit()


    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TProgressbar", thickness=25, troughcolor="#e0e0e0")

    def create_main_layout(self):
        self.main_container = tk.Frame(self.root, bg="#f0f2f5", padx=20, pady=20)
        self.main_container.pack(fill="both", expand=True)

        # 1. REGISTER PANEL (Matches your GUI)
        self.reg_frame = tk.LabelFrame(self.main_container, text=" Register ", font=("Arial", 14, "bold"), bg="white")
        self.reg_frame.place(relx=0.02, rely=0.05, relwidth=0.3, relheight=0.9)
        self.create_header(self.reg_frame, "Register", "#3b5998")
        tk.Label(self.reg_frame, text="Voter Name:", bg="white").pack(anchor="w", padx=20, pady=(60, 5))
        self.reg_name_entry = tk.Entry(self.reg_frame, font=("Arial", 12), bd=1, relief="solid")
        self.reg_name_entry.pack(fill="x", padx=20)
        tk.Button(self.reg_frame, text="Register Voter", bg="#5cb85c", fg="white", font=("Arial", 12, "bold"), command=self.register_voter).pack(fill="x", padx=20, pady=20)
        self.reg_status = tk.Label(self.reg_frame, text="", fg="#5cb85c", bg="white")
        self.reg_status.pack()

        # 2. VOTE PANEL
        self.vote_frame = tk.LabelFrame(self.main_container, text=" Vote ", font=("Arial", 14, "bold"), bg="white")
        self.vote_frame.place(relx=0.35, rely=0.05, relwidth=0.3, relheight=0.9)
        self.create_header(self.vote_frame, "Vote", "#f0ad4e")
        tk.Label(self.vote_frame, text="Registered Name:", bg="white").pack(anchor="w", padx=20, pady=(60, 5))
        self.vote_name_entry = tk.Entry(self.vote_frame, font=("Arial", 12), bd=1, relief="solid")
        self.vote_name_entry.pack(fill="x", padx=20)
        self.vote_buttons = []

        for c, color in [("A", "#d9534f"), ("B", "#d9534f"), ("C", "#5cb85c")]:
            btn = tk.Button(
                self.vote_frame,
                text=f"Vote Candidate {c}",
                bg=color,
                fg="white",
                font=("Arial", 12, "bold"),
                command=lambda cand=c: self.cast_vote(cand)
            )
            btn.pack(fill="x", padx=20, pady=10)
            self.vote_buttons.append(btn)


        # 3. RESULTS PANEL
        self.res_frame = tk.LabelFrame(self.main_container, text=" Results ", font=("Arial", 14, "bold"), bg="white")
        self.res_frame.place(relx=0.68, rely=0.05, relwidth=0.3, relheight=0.9)
        self.create_header(self.res_frame, "Results", "#4e5d6c")
        self.results_locked_label = tk.Label(self.res_frame, text="Results Hidden\nLogin as Admin", bg="white", pady=50)
        self.results_locked_label.pack()
        self.admin_btn = tk.Button(self.res_frame, text="Admin Login", command=self.show_admin_login)
        self.admin_btn.pack()
        self.prog_a = self.create_result_row(self.res_frame, "Candidate A", "blue")
        self.prog_b = self.create_result_row(self.res_frame, "Candidate B", "red")
        self.prog_c = self.create_result_row(self.res_frame, "Candidate C", "green")
        self.hide_results()

    def create_header(self, parent, text, color):
        h = tk.Frame(parent, bg=color, height=45)
        h.pack(fill="x", side="top")
        tk.Label(h, text=text, bg=color, fg="white", font=("Arial", 12, "bold")).pack(pady=10)

    def create_result_row(self, parent, label, color):
        f = tk.Frame(parent, bg="white", pady=10)
        lbl = tk.Label(f, text=f"{label}: 0 Votes", bg="white", font=("Arial", 10, "bold"))
        lbl.pack(anchor="w", padx=20)
        pb = ttk.Progressbar(f, orient="horizontal", length=200, mode="determinate")
        pb.pack(fill="x", padx=20, pady=5)
        return {"frame": f, "label": lbl, "bar": pb}

    def hide_results(self):
        for p in [self.prog_a, self.prog_b, self.prog_c]: p["frame"].pack_forget()

    # ---------- EMAIL OTP LOGIC ----------
    def show_verification_overlay(self):
        """Creates the startup window you see in your photo."""
        self.overlay = tk.Toplevel(self.root)
        self.overlay.configure(bg="#f0f2f5")
        self.overlay.title("Identity Verification")
        self.overlay.geometry("400x400")
        self.overlay.grab_set()
        card = tk.Frame(
            self.overlay,
            bg="white",
            padx=30,
            pady=30
        )
        card.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            card,
            text="Verify Your Email",
            font=("Arial", 18, "bold"),
            bg="white"
        ).pack(pady=(0, 5))
        tk.Label(
            card,
            text="Enter your email to receive a one-time verification code",
            font=("Arial", 10),
            fg="#666666",
            bg="white"
        ).pack(pady=(0, 20))
        tk.Label(
            card,
            text="Email Address",
            font=("Arial", 10, "bold"),
            bg="white"
        ).pack(anchor="w")
        self.email_input = tk.Entry(
            card,
            width=30,
            font=("Arial", 11),
            relief="solid",
            bd=1
        )
        self.email_input.insert(0, "ashith232@gmail.com") # Default from your pic
        self.email_input.pack(pady=(5,15))
        tk.Button(
            card,
            text="Send OTP",
            command=self.send_email_otp,
            bg="#e4e6eb",
            fg="black",
            font=("Arial", 11, "bold"),
            relief="flat",
            padx=10,
            pady=8
        ).pack(fill="x", pady=(0, 20))
        tk.Label(
            card,
            text="Enter OTP",
            font=("Arial", 10, "bold"),
            bg="white"
        ).pack(anchor="w")
        self.otp_input = tk.Entry(
            card,
            width=15,
            font=("Arial", 12),
            relief="solid",
            bd=1,
            justify="center"
        )
        self.otp_input.pack(pady=(5, 20))
        self.otp_input.pack(pady=5)
        tk.Button(
            card,
            text="Verify & Start Voting",
            command=self.verify_otp,
            bg="#3b5998",
            fg="white",
            font=("Arial", 12, "bold"),
            relief="flat",
            padx=10,
            pady=10
        ).pack(fill="x")
        tk.Label(
            card,
            text="🔒 Your email is used only for verification",
            font=("Arial", 9),
            fg="#888888",
            bg="white"
        ).pack(pady=(15, 0))

    def send_email_otp(self):
        """Uses SMTP to send the code using your App Password."""
        receiver = self.email_input.get().strip()
        self.current_otp = str(random.randint(100000, 999999))
        try:
            msg = EmailMessage()
            msg.set_content(f"Your Voting OTP is: {self.current_otp}")
            msg['Subject'] = "Secure Voting Verification"
            msg['From'] = self.SENDER_EMAIL
            msg['To'] = receiver
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                server.login(self.SENDER_EMAIL, self.APP_PASSWORD)
                server.send_message(msg)
            messagebox.showinfo("Success", f"OTP sent to {receiver}")
        except Exception as e:
            messagebox.showerror("Error", f"OTP Failed: {e}\nCheck App Password!")

    def verify_otp(self):
        if self.otp_input.get() == self.current_otp:
            self.overlay.destroy()
            self.root.deiconify()   # ✅ SHOW voting window
        else:
            messagebox.showerror("Error", "Incorrect OTP")


    # ---------- ADMIN LOGIN (Matches your popup) ----------
    def show_admin_login(self):
        self.admin_win = tk.Toplevel(self.root)
        self.admin_win.title("Admin Login")
        tk.Label(self.admin_win, text="Admin Username:").pack(pady=5)
        self.adm_u = tk.Entry(self.admin_win)
        self.adm_u.pack()
        tk.Label(self.admin_win, text="Admin Password:").pack(pady=5)
        self.adm_p = tk.Entry(self.admin_win, show="*")
        self.adm_p.pack()
        tk.Button(self.admin_win, text="Login as Admin", bg="#3b5998", fg="white", command=self.check_admin).pack(pady=20)

    def check_admin(self):
        if self.adm_u.get() == "admin" and self.adm_p.get() == "admin123":
            self.admin_win.destroy()
            self.results_locked_label.pack_forget()
            self.admin_btn.pack_forget()
            for p in [self.prog_a, self.prog_b, self.prog_c]: p["frame"].pack(fill="x")
            self.update_results_ui()
        else:
            messagebox.showerror("Error", "Invalid Credentials")

    def register_voter(self):
        name = self.reg_name_entry.get().strip()

        if not name:
            return

    # must contain at least one alphabet
        if not any(ch.isalpha() for ch in name):
            messagebox.showerror("Error", "Name must contain at least one alphabet")
            return

        try:
            self.cursor.execute("INSERT INTO voters (name) VALUES (?)", (name,))
            self.conn.commit()
            self.reg_status.config(text="Registration successful!")
            self.reg_name_entry.delete(0, tk.END)
        except:
            messagebox.showerror("Error", "Already Registered!")



    def cast_vote(self, candidate):
        name = self.vote_name_entry.get().strip()
        self.cursor.execute("SELECT has_voted FROM voters WHERE name=?", (name,))
        res = self.cursor.fetchone()
        if not res: messagebox.showerror("Error", "Name not registered!")
        elif res[0] == 1: messagebox.showerror("Error", "Already Voted!")
        else:
            self.cursor.execute("UPDATE results SET count = count + 1 WHERE candidate=?", (candidate,))
            self.cursor.execute("UPDATE voters SET has_voted = 1 WHERE name=?", (name,))
            self.conn.commit()
            messagebox.showinfo("Success", f"Vote cast for Candidate {candidate}!")
            self.update_results_ui()
            self.vote_name_entry.delete(0, tk.END)

# 🔒 Disable voting for 10 seconds
            for btn in self.vote_buttons:
                btn.config(state="disabled")

# ⏳ Re-enable after 10 seconds
            self.root.after(10000, self.enable_voting)

    def update_results_ui(self):
        self.cursor.execute("SELECT count FROM results ORDER BY candidate ASC")
        counts = [row[0] for row in self.cursor.fetchall()]
        total = sum(counts) or 1
        for count, ui, cand in zip(counts, [self.prog_a, self.prog_b, self.prog_c], ["A", "B", "C"]):
            ui["label"].config(text=f"Candidate {cand}: {count} Vote{'s' if count != 1 else ''}")
            ui["bar"]['value'] = (count / total) * 100

if __name__ == "__main__":
    root = tk.Tk()
    app = CompetitionVotingSystem(root)
    root.mainloop()
