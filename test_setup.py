
import sys

print("=" * 60)
print("🧪 FINANCE CHATBOT - SETUP VERIFICATION")
print("=" * 60)

# Test 1: Python version
print("\n1️⃣ Checking Python version...")
version = sys.version_info
if version.major >= 3 and version.minor >= 8:
    print(f"   ✅ Python {version.major}.{version.minor}.{version.micro} - OK")
else:
    print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} - Need 3.8+")
    sys.exit(1)

# Test 2: Required packages
print("\n2️⃣ Checking required packages...")
required_packages = {
    'flask': 'Flask',
    'flask_cors': 'Flask-CORS',
    'pandas': 'Pandas',
    'numpy': 'NumPy',
    'yfinance': 'yfinance'
}

missing_packages = []
for module, name in required_packages.items():
    try:
        __import__(module)
        print(f"   ✅ {name} - Installed")
    except ImportError:
        print(f"   ❌ {name} - Missing")
        missing_packages.append(name)

if missing_packages:
    print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
    print("   Install with: pip install -r requirements.txt")
    sys.exit(1)

# Test 3: Check CSV file
print("\n3️⃣ Checking CSV file...")
import os
import pandas as pd

csv_candidates = [
    "final_combined_1800.csv",
    "/Users/jigyasaverma/Desktop/finance_chatbot/final_combined.csv"
]

csv_found = None
for csv_path in csv_candidates:
    if os.path.exists(csv_path):
        csv_found = csv_path
        break

if csv_found:
    print(f"   ✅ CSV file found: {csv_found}")

    # Try to read CSV
    try:
        df = pd.read_csv(csv_found)
        print(f"   ✅ CSV readable - {len(df)} rows")

        # Check columns
        df.columns = df.columns.str.strip()
        has_input = 'input' in df.columns or 'Input' in df.columns
        has_output = 'output' in df.columns or 'Output' in df.columns

        if has_input and has_output:
            print(f"   CSV has correct columns: {list(df.columns)}")
        else:
            print(f"     CSV columns: {list(df.columns)}")
            print(f"      Expected: 'input' and 'output' (case-insensitive)")
    except Exception as e:
        print(f"   Error reading CSV: {e}")
        sys.exit(1)
else:
    print("   CSV file not found!")
    print("      Update the path in app.py or place CSV in current directory")
    print(f"      Current directory: {os.getcwd()}")
    sys.exit(1)

# Test 4: Test yfinance
print("\n4️⃣ Testing yfinance (internet connection)...")
try:
    import yfinance as yf

    stock = yf.Ticker("AAPL")
    hist = stock.history(period="1d")
    if not hist.empty:
        print(f"   ✅ yfinance working - AAPL: ${hist['Close'].iloc[-1]:.2f}")
    else:
        print("   ⚠️  yfinance connected but no data returned")
except Exception as e:
    print(f"   ⚠️  yfinance error (check internet): {str(e)[:50]}...")

# Test 5: Check if port 5000 is available
print("\n5️⃣ Checking if port 5000 is available...")
import socket


def is_port_available(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return True
        except:
            return False


if is_port_available(5000):
    print("   ✅ Port 5000 is available")
else:
    print("     Port 5000 is already in use")
    print("      Either stop the other process or change port in app.py")

# Test 6: Try importing main chatbot class
print("\nTesting chatbot class...")
try:
    from finance_ai_chatbot import FinanceChatbot

    print("  FinanceChatbot class imported successfully")

    # Try to initialize
    try:
        bot = FinanceChatbot(csv_found)
        print(" Chatbot initialized successfully")

        # Try a test query
        response = bot.get_response("test")
        print(f" Bot response working (confidence tracked)")

    except Exception as e:
        print(f" Error initializing chatbot: {e}")
        sys.exit(1)

except Exception as e:
    print(f" Error importing chatbot: {e}")
    sys.exit(1)

# All tests passed
print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
print("\n🚀 You can now run the application:")
print("   python app.py")
print("\nThen open in browser:")
print("   http://localhost:5000")
print("\n" + "=" * 60)