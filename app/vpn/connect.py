# def try_connect_ovpn_config(ovpn_text, timeout=60):
#     with NamedTemporaryFile("w", suffix=".ovpn", delete=False) as f:
#         f.write(ovpn_text)
#         ovpn_path = f.name

#     try:
#         proc = subprocess.Popen(
#             ["sudo", "openvpn", "--config", ovpn_path],
#             stdout=subprocess.PIPE,
#             stderr=subprocess.STDOUT,
#             text=True
#         )

#         t_start = time.time()
#         while time.time() - t_start < timeout:
#             line = proc.stdout.readline()
#             if "Initialization Sequence Completed" in line:
#                 print("[+] Connected successfully!")
#                 proc.terminate()
#                 return True
#             if "TLS Error" in line or "Connection refused" in line:
#                 break
#         proc.terminate()
#         return False
#     finally:
#         os.remove(ovpn_path)