# Initialize Coinbase CDP Wallet Context with error logging
cdp_context = "CDP SDK not initialized."
if CDP_AVAILABLE:
    try:
        Cdp.configure("955d09f4-d942-4272-89dc-5799d8d5c0bd", "T7FSym8hkHNYlfQWAUFzvlPi/HtjJllsF9BsE3QcPvXysaL1Gm/OopzgPa2NABll001B+TjivSK/eXQLP4kg==")
        wallet = Wallet.create()
        cdp_context = f"Active CDP Wallet Address: {wallet.get_address().getId()} | Network: Base-Sepolia | Connected Successfully"
    except Exception as e:
        cdp_context = f"CDP Init Error: {type(e).__name__}: {e}"
else:
    # Try to capture why it's not available
    try:
        import cdp
        cdp_context = "CDP module imported after check failed."
    except Exception as import_err:
        cdp_context = f"CDP Import Failure: {import_err}"
