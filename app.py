import streamlit as st
import pandas as pd
import io

# ---------------- CONFIGURATION ---------------- #
st.set_page_config(page_title="Snapdeal Pricing Tool", layout="centered")

GST = 0.18
SLM_RATE = 0.06
MF_RATE = 0.001
ROYALTY_RATE = 0.10  # 10%

# ---------------- LOGIC FUNCTIONS ---------------- #
def slab_fee(weight):
    if weight <= 500:
        return 75
    elif weight <= 1000:
        return 115
    elif weight <= 1500:
        return 155
    elif weight <= 2000:
        return 195
    elif weight <= 2500:
        return 235
    elif weight <= 3000:
        return 275
    else:
        extra = ((weight - 3000) // 500 + 1) * 10
        return 275 + extra

# ---------------- UI HEADER ---------------- #
st.title("UNO PLUS – Fixed Profit Pricing Tool")
st.markdown("**Note:** Final Profit = Target Profit even after 10% Royalty (DKUC / MKUC)")
st.markdown("---")

# ---------------- SECTION 1: DOWNLOAD TEMPLATE ---------------- #
st.subheader("Step 1: Download Input Template")

# Template Dataframe create karna
template_df = pd.DataFrame(columns=[
    "SKU",
    "Cost_Price",
    "Weight_gms",
    "Target_Profit_Rs"
])

# Excel file ko memory mein save karna (kyunki web pe direct save nahi hota)
buffer_template = io.BytesIO()
with pd.ExcelWriter(buffer_template, engine='xlsxwriter') as writer:
    template_df.to_excel(writer, index=False)
    
st.download_button(
    label="📥 Download Template (.xlsx)",
    data=buffer_template.getvalue(),
    file_name="Input_Template.xlsx",
    mime="application/vnd.ms-excel"
)

st.markdown("---")

# ---------------- SECTION 2: PROCESS FILE ---------------- #
st.subheader("Step 2: Upload File & Generate")

uploaded_file = st.file_uploader("Upload your filled Excel file", type=["xlsx"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        
        # Check if required columns exist
        required_cols = ["SKU", "Cost_Price", "Weight_gms", "Target_Profit_Rs"]
        if not all(col in df.columns for col in required_cols):
            st.error(f"Error: File must contain these columns: {required_cols}")
        else:
            output = []
            
            # Progress bar (optional styling)
            my_bar = st.progress(0)
            total_rows = len(df)

            for index, r in df.iterrows():
                # Logic same as your original script
                sku = str(r["SKU"])
                cost = r["Cost_Price"]
                weight = r["Weight_gms"]
                target_profit = r["Target_Profit_Rs"]

                slab = slab_fee(weight)
                slab_gst = slab * GST

                # Platform %
                base_pct = SLM_RATE + MF_RATE
                platform_effective_pct = base_pct + (base_pct * GST)

                # Royalty %
                royalty_pct = ROYALTY_RATE if (
                    sku.strip().upper().startswith("DKUC") or sku.strip().upper().startswith("MKUC")
                ) else 0

                # Reverse selling price calculation
                selling_price = (
                    cost + target_profit + slab + slab_gst
                ) / (1 - platform_effective_pct - royalty_pct)

                # Charges Breakdown
                monetization = selling_price * SLM_RATE
                monetization_gst = monetization * GST

                marketing_fee = selling_price * MF_RATE
                marketing_fee_gst = marketing_fee * GST

                total_charges = (
                    monetization + monetization_gst +
                    marketing_fee + marketing_fee_gst +
                    slab + slab_gst
                )

                net_payout = selling_price - total_charges
                royalty = selling_price * royalty_pct
                final_payout = net_payout - royalty
                final_profit = final_payout - cost

                output.append([
                    sku,
                    round(cost, 2),
                    weight,
                    round(target_profit, 2),
                    round(selling_price, 2),
                    round(total_charges, 2),
                    round(royalty, 2),
                    round(final_payout, 2),
                    round(final_profit, 2)
                ])
                
                # Update progress bar
                my_bar.progress((index + 1) / total_rows)

            # Create Output DataFrame
            out_df = pd.DataFrame(output, columns=[
                "SKU",
                "Cost_Price",
                "Weight_gms",
                "Target_Profit_Rs",
                "Suggested_Selling_Price",
                "Total_Charges (No Royalty)",
                "Royalty_10%",
                "Final_Payout",
                "Final_Profit"
            ])

            st.success("Calculation Complete! Preview below:")
            st.dataframe(out_df.head()) # Show top 5 rows

            # Save Output to Memory Buffer
            buffer_output = io.BytesIO()
            with pd.ExcelWriter(buffer_output, engine='xlsxwriter') as writer:
                out_df.to_excel(writer, index=False)

            # Download Button for Result
            st.download_button(
                label="✅ Download Calculated File",
                data=buffer_output.getvalue(),
                file_name="Processed_Pricing_File.xlsx",
                mime="application/vnd.ms-excel"
            )

    except Exception as e:
        st.error(f"An error occurred: {e}")
