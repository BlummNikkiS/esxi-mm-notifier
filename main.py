import time
import configparser
import requests
import logging
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import atexit
import ssl

CFG_FILE = "config.ini"
CHECK_INTERVAL = 60  # секунды

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def load_config():
    cfg = configparser.ConfigParser()
    cfg.read(CFG_FILE)
    vcenter_cfg = cfg['vcenter']
    telegram_cfg = cfg['telegram']
    token = telegram_cfg['token']
    chat_ids = [i.strip() for i in telegram_cfg['chat_ids'].split(',') if i.strip()]
    return vcenter_cfg, token, chat_ids

def send_telegram(token, chat_ids, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    for chat_id in chat_ids:
        try:
            resp = requests.post(url, data={'chat_id': chat_id, 'text': text}, timeout=10)
            if resp.ok:
                logging.info(f"Уведомление отправлено в chat_id {chat_id}")
            else:
                logging.warning(f"Ошибка отправки в chat_id {chat_id}: {resp.text}")
        except requests.RequestException as e:
            logging.error(f"Ошибка отправки Telegram: {e}")

def get_host_states(vcenter_cfg):
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    try:
        si = SmartConnect(
            host=vcenter_cfg['host'],
            user=vcenter_cfg['user'],
            pwd=vcenter_cfg['password'],
            sslContext=ssl_context
        )
    except Exception as e:
        logging.error(f"Ошибка подключения к vCenter: {e}")
        raise
    atexit.register(Disconnect, si)
    content = si.RetrieveContent()
    hosts = content.viewManager.CreateContainerView(content.rootFolder, [vim.HostSystem], True).view
    states = {host.name: bool(host.runtime.inMaintenanceMode) for host in hosts}
    Disconnect(si)
    return states

def monitor():
    vcenter_cfg, token, chat_ids = load_config()
    last_states = {}
    while True:
        try:
            cur_states = get_host_states(vcenter_cfg)
            for hostname, in_maint in cur_states.items():
                prev_maint = last_states.get(hostname)
                if prev_maint is None:
                    logging.info(f"Хост {hostname} — начальное состояние: {'Режим обслуживания' if in_maint else 'Обычный режим'}")
                elif prev_maint is False and in_maint is True:
                    send_telegram(token, chat_ids, f"Хост {hostname} был переведён в режим обслуживания.")
                    logging.info(f"Уведомление: {hostname} вошёл в обслуживание")
                elif prev_maint is True and in_maint is False:
                    send_telegram(token, chat_ids, f"Хост {hostname} выведен из режима обслуживания.")
                    logging.info(f"Уведомление: {hostname} вышел из обслуживания")
            last_states = cur_states
        except Exception as e:
            send_telegram(token, chat_ids, f"Ошибка мониторинга ESXi: {e}")
            logging.error(f"Мониторинг прерван ошибкой: {e}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    monitor()