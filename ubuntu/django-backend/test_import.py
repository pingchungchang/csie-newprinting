try:
    from api.newprinting_grpc.bridge.printer_client import PrinterClient
    print("[Import Success]")

    # test client init
    client = PrinterClient()
    print("[Client Init Success]")
except Exception as e:
    print(f"[Import Failed] {e}")
