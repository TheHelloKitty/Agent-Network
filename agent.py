# Add this near the top or update your existing logging logic in agent.py
uploaded_items = []
issues_list = []

# Inside your main execution loop for products:
for prod in generation_products:
    name = prod["name"]
    price = prod["price_cents"]
    desc = prod["description"]

    try:
        # Push to Gumroad
        if name in existing_gumroad:
            log_lines.append(f"  - Gumroad: Skipped [{name}] (Already Exists)")
        else:
            g_res = create_gumroad_product(name, desc, price, gumroad_token)
            if g_res and "product" in g_res:
                gumroad_new += 1
                uploaded_items.append(f"Gumroad: {name}")
            else:
                issues_list.append(f"Gumroad upload failed or skipped for: {name}")

        # Push to Lemon Squeezy
        if name in existing_lemon:
            log_lines.append(f"  - Lemon Squeezy: Skipped [{name}] (Already Exists)")
        else:
            l_res = create_lemon_squeezy_product(name, desc, ls_api_key, ls_store_id)
            if l_res and "data" in l_res:
                lemon_new += 1
                uploaded_items.append(f"Lemon Squeezy: {name}")
            else:
                issues_list.append(f"Lemon Squeezy upload failed or skipped for: {name}")
                
    except Exception as e:
        issues_list.append(f"Exception encountered for {name}: {str(e)}")

# At the very end of your script, print a clear breakdown
print("\n" + "="*40)
print("📊 AGENT UPLOAD REPORT")
print("="*40)
print(f"Total Successfully Uploaded This Run: {len(uploaded_items)}")
for item in uploaded_items:
    print(f"  ✅ {item}")

print("\n" + "="*40)
print("⚠️ RUN ISSUES & WARNINGS")
print("="*40)
if len(issues_list) == 0:
    print("  🎉 Zero issues detected! All operations nominal.")
else:
    for issue in issues_list:
        print(f"  ❌ {issue}")
print("="*40)
