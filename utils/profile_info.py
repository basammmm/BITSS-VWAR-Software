from tkinter import Frame, Label, Button
from datetime import datetime, timedelta

# Static bullet terms
LICENSE_TERMS = [
    "🔄 Your license auto-renews on the expiration date.",
    "💳 Payment is due within 7 days after renewal.",
    "⚠️ If unpaid, your license will be suspended.",
    "💰 Reactivation Fee: €25 + annual license cost.",
    "❌ Cancel auto-renewal at least 30 days before expiration.",
    "📬 Support: support@bobosohomail.com",
    "🌐 Website: www.bitss.fr"
]

# Status-based messages with {date} placeholder
LICENSE_MESSAGES = {
    "active": "✅ Your license is active. Valid till {date}.",
    "expiring_soon": "⚠️ Your license will expire on {date}. Please renew soon.",
    "renewed_but_unpaid": "⏳ Your license was renewed on {date} but payment is pending.",
    "suspended": "❌ Your license was suspended after {date}. Contact support.",
    "invalid": "⚠️ License data missing or unreadable."
}


class LicenseTermsPage(Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="white")
        
        activated_user = controller.activated_user

        valid_till = controller.valid_till
        
        created_at = controller.created_at

        # Validate and compute license status
        try:
            print("[DEBUG] valid_till from controller:", valid_till)

            # datetime.strptime(valid_till, "%Y-%m-%d")
            
            
            # Try parsing full datetime first, then extract only date
            try:
                parsed_date = datetime.strptime(valid_till, "%Y-%m-%d %H:%M:%S").date()
            except ValueError:
                parsed_date = datetime.strptime(valid_till, "%Y-%m-%d").date()

            # status = self.get_license_status(parsed_date)
            status = self.get_license_status(parsed_date.strftime("%Y-%m-%d"))

        except Exception:
            status = "invalid"

        message = LICENSE_MESSAGES.get(status, "").format(
            date=valid_till if status != "invalid" else "N/A"
        )

        # Dynamic message

        
        Label(self, text="📜 VWAR License Terms", font=("Arial", 18, "bold"),
                    bg="white", fg="#333").pack(pady=10)
        
        
        # Header
        Label(self, text=f"USER : {activated_user}", font=("Arial", 18, "bold"),
              bg="white", fg="#333").pack(pady=10)
        
        Label(self, text=f"Created AT : {created_at}", font=("Arial", 18, "bold"),
              bg="white", fg="#333").pack(pady=10)
        
        Label(self, text=message, font=("Arial", 14, "bold"),
              bg="white", fg="red").pack(pady=20)
        

        # Bullet list
        # for t in LICENSE_TERMS:
        #     Label(self, text=t, font=("Arial", 12), anchor="w",
        #           bg="white", fg="black", wraplength=800, justify="left").pack(padx=40, anchor="w", pady=4)

        # Back button
        Button(self, text="⬅ Back to Home", font=("Arial", 12),
               command=lambda: controller.show_page("home")).pack(pady=20)

    def get_license_status(self, valid_till_str):
        today = datetime.today().date()
        try:
            expiry = datetime.strptime(valid_till_str, "%Y-%m-%d").date()
        except Exception:
            return "invalid"

        if today > expiry + timedelta(days=7):
            return "suspended"
        elif today > expiry:
            return "renewed_but_unpaid"
        elif expiry - today <= timedelta(days=7):
            return "expiring_soon"
        else:
            return "active"
