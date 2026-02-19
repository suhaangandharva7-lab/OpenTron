import os
import sys

def bootstrap():
    print("🚥 Redirecting to OpenTron Onboarding Protocol...")
    import onboard
    onboard.main()

if __name__ == "__main__":
    bootstrap()
