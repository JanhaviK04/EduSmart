import streamlit as st
import pyrebase
from datetime import datetime
from streamlit_option_menu import option_menu
import streamlit.components.v1 as components
from web3 import Web3

# Set page configuration
st.set_page_config(initial_sidebar_state="collapsed")

# Firebase configuration
firebaseConfig = {
    'apiKey': "AIzaSyCZPtwe0V9lMRTqUEqDcPKFALHwlefAmho",
    'authDomain': "courserecsystem-9a84c.firebaseapp.com",
    'projectId': "courserecsystem-9a84c",
    'databaseURL': "https://courserecsystem-9a84c-default-rtdb.europe-west1.firebasedatabase.app/",
    'storageBucket': "courserecsystem-9a84c.appspot.com",
    'messagingSenderId': "149618883518",
    'appId': "1:149618883518:web:0d6c9b123973bf5e1cd7ef",
    'measurementId': "G-YCFDDD2VLR"
}

# Initialize Firebase
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
db = firebase.database()
storage = firebase.storage()

# Connect to Ethereum
alchemy_url = 'https://eth-sepolia.g.alchemy.com/v2/hJrUEXhm5z99RyGCJgM2jlS-9LQb_HsD'
web3 = Web3(Web3.HTTPProvider(alchemy_url))

# Smart Contract ABI and Address
contract_address = '0xA41588C7E3D6B16963C2c80B21807B77271cFF0a'
contract_abi = [
    {
        "inputs": [
            {"internalType": "string", "name": "email", "type": "string"},
            {"internalType": "string", "name": "password", "type": "string"},
            {"internalType": "string", "name": "username", "type": "string"},
            {"internalType": "string", "name": "field", "type": "string"}
        ],
        "name": "registerUser",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

contract = web3.eth.contract(address=contract_address, abi=contract_abi)

# Display styling
st.markdown("""
<style>
.button {
    display: inline-block;
    padding: 10px 20px;
    background-color: #b153ea;
    color: #fff;
    text-align: center;
    text-decoration: none;
    border-radius: 5px;
    cursor: pointer;
}
</style>
""", unsafe_allow_html=True)

def is_user_logged_in():
    try:
        user = auth.current_user
        return user is not None
    except:
        return False


def register_user_on_blockchain(email, password, username, field):
    try:
        # Get user's account (address)
        account = web3.eth.account.from_key('c0740413c78bea659c6d67677b039482ee2b5151fc1d348dd3e64602989d8b24')

        if not web3.is_connected():
            st.error("Failed to connect to Ethereum network")
            return

        nonce = web3.eth.get_transaction_count(account.address)

        # Prepare the transaction data using the contract function call
        transaction_data = contract.functions.registerUser(email, password, username, field)._encode_transaction_data()

        # Prepare the transaction manually
        tx = {
            'from': account.address,
            'to': contract_address,
            'gas':  500000,
            'gasPrice': web3.to_wei('10', 'gwei'),  
            'nonce': nonce,
            'chainId': 11155111,  # Sepolia Chain ID
            'data': transaction_data  # Encoded transaction data
        }

        # Sign the transaction
        signed_tx = web3.eth.account.sign_transaction(tx, account.key)

        # Send the transaction
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return tx_hash.hex()

    except Exception as e:
        st.error(f"Error registering user on blockchain: {str(e)}")
        st.error(f"Full Error: {e}")



def app():
    st.markdown("<h1 style='text-align: center; font-size:80px ; font-weight:30px;margin:0px;padding:0px; color: #6f07bb;'>EduSmart</h1><br><center><p style='font-size:25px;font-weight: normal; font-style:italic;color: #fffff'>Where learning meets personalisation</center>", unsafe_allow_html=True)
    
    if not is_user_logged_in():
        choice = option_menu(None, ["Login", "Signup"], orientation='horizontal')

        if choice == "Signup":
            st.subheader("Signup")
            email = st.text_input("Email:")
            create_password = st.text_input("Create Password:", type="password")
            confirm_password = st.text_input("Confirm Password:", type="password")
            username = st.text_input('Username', value='Default')
            field = st.selectbox("Education Field:", ["Medicine", "Computer Science", "Engineering", "Commerce", "Arts", "Marketing"])

            if create_password != confirm_password:
                st.error("Passwords do not match")
            if st.button("Signup"):
                try:
                    user = auth.create_user_with_email_and_password(email, confirm_password)
                    st.success('Your account is created successfully!')

                    # Sign in
                    user = auth.sign_in_with_email_and_password(email, confirm_password)

                    # Store the user's local ID in session_state
                    st.session_state.user_local_id = user['localId']
                    st.session_state.user = user

                    db.child(user['localId']).child("Username").set(username)
                    db.child(user['localId']).child("ID").set(user['localId'])

                    # Register user on the blockchain
                    tx_hash = register_user_on_blockchain(email, confirm_password, username, field)
                    st.success(f'User registered on blockchain with transaction hash: {tx_hash}')

                    st.title('Welcome ' + username)
                    st.info('Login via login drop down selection')
                except Exception as e:
                    st.error(f"Signup Failed: {str(e)}")

        elif choice == "Login":
            st.subheader("Login")
            email = st.text_input("Email:")
            password = st.text_input("Password:", type="password")

            if st.button('Login'):
                try:
                    user = auth.sign_in_with_email_and_password(email, password)
                    st.success("Login Successful")
                    st.markdown(f'<a href="Dashboard?user_id={user["localId"]}" target="_self" class="button">Get Started</a>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Login Failed: {str(e)}")

if __name__ == "__main__":
    app()
