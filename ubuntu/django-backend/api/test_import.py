try:
    from newprinting_grpc.bridge.printer_client import PrinterClient
    from newprinting_balance.balance_calculator import query_balance, safe_withdraw
    print("[Import Success]")
except Exception as e:
    print(f"[Import Failed] {e}")
