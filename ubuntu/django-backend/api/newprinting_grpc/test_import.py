try:
    from bridge.printer_client import PrinterClient
    print("[Import Success]")
except Exception as e:
    print(f"[Import Failed] {e}")
