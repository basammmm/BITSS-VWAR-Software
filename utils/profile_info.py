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
        
        # Auto-Renew Status - Dynamic label that updates based on controller's auto_renew_var
        self.auto_renew_status_label = Label(self, text="", font=("Arial", 14, "bold"),
                                             bg="white")
        self.auto_renew_status_label.pack(pady=10)
        
        # Store reference to controller for updates
        self.controller = controller
        
        # Update the auto-renew display
        self.update_auto_renew_display()
        

        # Bullet list
        # for t in LICENSE_TERMS:
        #     Label(self, text=t, font=("Arial", 12), anchor="w",
        #           bg="white", fg="black", wraplength=800, justify="left").pack(padx=40, anchor="w", pady=4)

        # Back button
        Button(self, text="⬅ Back to Home", font=("Arial", 12),
               command=lambda: controller.show_page("home")).pack(pady=20)
    
    def update_auto_renew_display(self):
        """Update the auto-renew status display based on controller's current value."""
        try:
            # Get current value from controller's auto_renew_var
            if hasattr(self.controller, 'auto_renew_var'):
                current_value = self.controller.auto_renew_var.get()
                auto_renew_enabled = (current_value == "YES")
            else:
                # Fallback to fetching from database if controller doesn't have the var
                from activation.license_utils import get_auto_renew_status
                auto_renew_enabled = get_auto_renew_status()
            
            auto_renew_text = "✅ Auto-Renew: Enabled" if auto_renew_enabled else "❌ Auto-Renew: Disabled"
            auto_renew_color = "green" if auto_renew_enabled else "red"
            
            self.auto_renew_status_label.config(text=auto_renew_text, fg=auto_renew_color)
            
            # Schedule next update in 1 second to keep it in sync
            self.after(1000, self.update_auto_renew_display)
        except Exception as e:
            # If there's an error, just stop updating
            print(f"[DEBUG] Error updating auto-renew display: {e}")
            pass

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
