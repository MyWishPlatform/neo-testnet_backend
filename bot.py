from time import sleep
import traceback
import hashlib
import base58
from jsonrpc_requests import Server
import telegram
from telegram.error import NetworkError, Unauthorized

from app.models import AssetsRequest
from app.db_restrictions import DatabaseRestrictions

from settings_local import BOT_TOKEN, FAUCET_CLI

ADDRESS_VERSION = 23

def double_hash(data):
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()

def check_address(text):
    try:
        bin_addr = base58.b58decode(text)
    except:
        return False
    return all([
            len(bin_addr) == 25,
            bin_addr[0] == ADDRESS_VERSION,
            double_hash(bin_addr[:21])[:4] == bin_addr[-4:]
    ])

def send_funds(address):
    node.sendfaucetassets(address)

def work(bot):
    global update_id
    for update in bot.get_updates(offset=update_id, timeout=10):
        update_id = update.update_id + 1
        if update.message:
            if not check_address(update.message.text):
                update.message.reply_text('Please enter correct NEO address')
                continue
            address = update.message.text
        
            asset_request = DatabaseRestrictions.find_address(address)
            if asset_request is not None and not DatabaseRestrictions.is_enough_time(asset_request.last_request_date):
                update.message.reply_text('This address was used recently. Please wait before next request')
                continue
            try:
                send_funds(address)
                if asset_request:
                    DatabaseRestrictions.update_request(asset_request)
                else:
                    DatabaseRestrictions.store_address(DatabaseRestrictions.new_entry(address))
                update.message.reply_text('Your funds sucessfully sent')
            except:
                traceback.print_exc()
                update.message.reply_text('Some error. Try later or contact support')





node = Server(FAUCET_CLI)
update_id = None
bot = telegram.Bot(BOT_TOKEN)


try:
    update_id = bot.get_updates()[0].update_id
except IndexError:
    update_id = None

while True:
    try:
        work(bot)
    except NetworkError:
        sleep(1)
    except Unauthorized:
        update_id += 1

