FROM python:3.11-slim

# أدوات الأمن الأساسية
RUN apt-get update && apt-get install -y --no-install-recommends \
        nmap curl wget git unzip whois dnsutils \
    && rm -rf /var/lib/apt/lists/*

# nuclei + httpx + katana (ProjectDiscovery)
RUN wget -q https://github.com/projectdiscovery/nuclei/releases/download/v3.3.0/nuclei_3.3.0_linux_amd64.zip -O /tmp/n.zip \
 && unzip -o /tmp/n.zip -d /usr/local/bin && rm /tmp/n.zip && chmod +x /usr/local/bin/nuclei
RUN wget -q https://github.com/projectdiscovery/httpx/releases/download/v1.6.0/httpx_1.6.0_linux_amd64.zip -O /tmp/h.zip \
 && unzip -o /tmp/h.zip -d /usr/local/bin && rm /tmp/h.zip && chmod +x /usr/local/bin/httpx
RUN wget -q https://github.com/projectdiscovery/katana/releases/download/v1.1.0/katana_1.1.0_linux_amd64.zip -O /tmp/k.zip \
 && unzip -o /tmp/k.zip -d /usr/local/bin && rm /tmp/k.zip && chmod +x /usr/local/bin/katana
RUN nuclei -update-templates

# sqlmap
RUN git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git /opt/sqlmap \
 && ln -s /opt/sqlmap/sqlmap.py /usr/local/bin/sqlmap && chmod +x /usr/local/bin/sqlmap

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# ملاحظة: Metasploit غير مثبَّت هنا عمدًا — الأداة تتصل بـ msfrpcd يعمل على
# مضيف Kali عبر الشبكة (راجع core/msf_client.py)، بدل تضمين MSF داخل الحاوية.

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

CMD ["python", "main.py"]
