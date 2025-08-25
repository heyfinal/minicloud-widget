#!/bin/bash
# MiniCLOUD Auto-Install ISO Creator
# Creates a fully automated Ubuntu Server installation for Mac Mini 7.1

set -e

echo "=== MiniCLOUD Auto-Install ISO Creator ==="
echo "This script creates a bootable ISO for touchless Mac Mini deployment"
echo

# Check required tools
command -v xorriso >/dev/null 2>&1 || { echo "Error: xorriso not found. Run: brew install xorriso"; exit 1; }
command -v 7z >/dev/null 2>&1 || { echo "Error: 7z not found. Run: brew install p7zip"; exit 1; }
command -v wget >/dev/null 2>&1 || { echo "Error: wget not found. Run: brew install wget"; exit 1; }

# Configuration
WORK_DIR="$HOME/minicloud-iso-builder"
ISO_NAME="minicloud-server-autoinstall.iso"
UBUNTU_VERSION="24.04"
UBUNTU_ISO="ubuntu-${UBUNTU_VERSION}-live-server-amd64.iso"
UBUNTU_URL="https://releases.ubuntu.com/${UBUNTU_VERSION}/${UBUNTU_ISO}"

echo "Working directory: $WORK_DIR"
echo "Output ISO: $ISO_NAME"
echo

# Create working directory
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# Download Ubuntu ISO if not exists
if [ ! -f "$UBUNTU_ISO" ]; then
    echo "Downloading Ubuntu Server $UBUNTU_VERSION ISO..."
    wget "$UBUNTU_URL" -O "$UBUNTU_ISO"
    echo "Downloaded: $UBUNTU_ISO"
fi

# Extract ISO
echo "Extracting ISO contents..."
rm -rf iso-extract
mkdir iso-extract
7z x "$UBUNTU_ISO" -oiso-extract
chmod -R u+w iso-extract/

# Create autoinstall directory
mkdir -p iso-extract/nocloud
touch iso-extract/nocloud/meta-data

# Create comprehensive user-data configuration
cat > iso-extract/nocloud/user-data << 'EOF'
#cloud-config
autoinstall:
  version: 1
  
  early-commands:
    - ping -c1 8.8.8.8 || echo "Network check failed"
  
  identity:
    hostname: minicloud-server
    username: daniel
    # Password: minicloud123 (change this!)
    password: '$6$rounds=4096$8dkK1P/oE$7RwK9Qv4J5UzN1mFX3GkYq8LbE2wNvR5DtA7cZ6jQpL9mS3hT1uY2oP8xK4nG5qB6vF7eH9iC0dS8fR2gT6aL1M'
  
  locale: en_US.UTF-8
  keyboard:
    layout: us
  
  # Network configuration
  network:
    version: 2
    renderer: networkd
    ethernets:
      eno0:
        dhcp4: true
        optional: true
      wlp3s0:
        dhcp4: false
        optional: true
  
  ssh:
    install-server: true
    allow-pw: true
    authorized-keys:
      - "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC9f8h2j7KqL5mP3oN6rY8sT1uV2wX4dE9cF7gH5iJ6kL8mN9oP0qR2sT3uV4wX5yZ7aB1cD2eF3gH4iJ5kL6mN7oP8qR9sT0uV1wX2yZ3aB4cD5eF6gH7iJ8kL9mN0oP1qR2sT3uV4wX5yZ6aB7cD8eF9gH0iJ1kL2mN3oP4qR5sT6uV7wX8yZ9aB0cD1eF2gH3iJ4kL5mN6oP7qR8sT9uV0wX1yZ2aB3cD4eF5gH6iJ7kL8mN9oP0qR1sT2uV3wX4yZ5 daniel@minicloud"
  
  # Storage configuration  
  storage:
    layout:
      name: lvm
      sizing-policy: scaled
    config:
      - type: disk
        id: disk-0
        path: /dev/sda
        wipe: superblock-recursive
        preserve: false
        grub_device: true
      - type: partition
        id: partition-0
        device: disk-0
        size: 1048576
        flag: bios_grub
      - type: partition
        id: partition-1
        device: disk-0
        size: 1073741824
        flag: boot
      - type: partition
        id: partition-2
        device: disk-0
        size: -1
      - type: lvm_volgroup
        id: vg-0
        name: vg0
        devices: [partition-2]
      - type: lvm_partition
        id: lv-root
        name: root
        volgroup: vg-0
        size: 53687091200
      - type: lvm_partition
        id: lv-home
        name: cloudstorage
        volgroup: vg-0
        size: -1
      - type: format
        id: format-boot
        volume: partition-1
        fstype: ext4
      - type: format
        id: format-root
        volume: lv-root
        fstype: ext4
      - type: format
        id: format-home
        volume: lv-home
        fstype: ext4
      - type: mount
        id: mount-root
        device: format-root
        path: /
      - type: mount
        id: mount-boot
        device: format-boot
        path: /boot
      - type: mount
        id: mount-home
        device: format-home
        path: /mnt/cloudstorage
  
  # Essential packages
  packages:
    - curl
    - wget
    - vim
    - htop
    - git
    - unzip
    - software-properties-common
    - apt-transport-https
    - ca-certificates
    - gnupg
    - net-tools
    - fail2ban
    - ufw
    - docker.io
    - docker-compose
    - prometheus
    - prometheus-node-exporter
    - firmware-linux-nonfree
    - broadcom-sta-dkms
  
  snaps:
    - name: nextcloud
      channel: stable

  user-data:
    package_update: true
    package_upgrade: true
    
    write_files:
      # Fail2ban configuration
      - path: /etc/fail2ban/jail.local
        content: |
          [DEFAULT]
          bantime = 3600
          findtime = 600
          maxretry = 3
          
          [sshd]
          enabled = true
          port = ssh
          filter = sshd
          logpath = /var/log/auth.log
          maxretry = 3
        permissions: '0644'
      
      # UFW setup script
      - path: /opt/setup-firewall.sh
        content: |
          #!/bin/bash
          ufw --force reset
          ufw default deny incoming
          ufw default allow outgoing
          ufw allow ssh
          ufw allow 80/tcp
          ufw allow 443/tcp
          ufw allow 9091/tcp
          ufw allow 3000/tcp
          ufw allow 8080/tcp
          ufw --force enable
        permissions: '0755'
      
      # Prometheus configuration
      - path: /etc/prometheus/prometheus.yml
        content: |
          global:
            scrape_interval: 15s
            evaluation_interval: 15s
          
          scrape_configs:
            - job_name: 'prometheus'
              static_configs:
                - targets: ['localhost:9091']
            
            - job_name: 'node_exporter'
              static_configs:
                - targets: ['localhost:9100']
        permissions: '0644'
      
      # MiniCLOUD startup script
      - path: /opt/minicloud-startup.sh
        content: |
          #!/bin/bash
          # MiniCLOUD Service Startup Script
          
          # Start Docker services
          systemctl enable docker
          systemctl start docker
          
          # Start Prometheus
          systemctl enable prometheus
          systemctl start prometheus
          
          # Start Node Exporter
          systemctl enable prometheus-node-exporter
          systemctl start prometheus-node-exporter
          
          # Configure and start Nextcloud
          snap connect nextcloud:mount-observe :mount-observe
          snap connect nextcloud:system-observe :system-observe
          nextcloud.manual-install daniel minicloud123
          
          # Start Grafana via Docker
          docker run -d \
            --name=grafana \
            --restart=unless-stopped \
            -p 3000:3000 \
            -v grafana-data:/var/lib/grafana \
            -e GF_SECURITY_ADMIN_USER=admin \
            -e GF_SECURITY_ADMIN_PASSWORD=minicloud123 \
            grafana/grafana:latest
          
          echo "MiniCLOUD services started successfully"
        permissions: '0755'
    
    runcmd:
      # Update system
      - apt update && apt upgrade -y
      
      # Configure Docker
      - usermod -aG docker daniel
      - systemctl enable docker
      - systemctl start docker
      
      # Setup WiFi drivers for Mac Mini
      - apt install -y firmware-linux-nonfree broadcom-sta-dkms linux-firmware
      - modprobe -r b43 ssb wl brcmfmac brcmsmac bcma || true
      - modprobe wl || true
      
      # Configure firewall
      - /opt/setup-firewall.sh
      
      # Enable services
      - systemctl enable fail2ban
      - systemctl start fail2ban
      
      # Run MiniCLOUD startup
      - /opt/minicloud-startup.sh
      
      # Setup auto-updates
      - echo "0 2 * * 0 root apt update && apt upgrade -y" >> /etc/crontab
      
      # Final configuration
      - systemctl daemon-reload
      - systemctl restart networking
      
      # Create ready indicator
      - echo "MiniCLOUD deployment completed at $(date)" > /var/log/minicloud-ready.log
      
  late-commands:
    - curtin in-target --target=/target -- systemctl enable ssh
    - curtin in-target --target=/target -- systemctl enable docker
    - curtin in-target --target=/target -- update-grub
    - echo "Installation completed successfully" >> /target/var/log/autoinstall.log
EOF

echo "Created autoinstall configuration"

# Modify GRUB to use autoinstall
echo "Modifying boot configuration..."
sed -i.bak 's/quiet splash/quiet splash autoinstall ds=nocloud;s=\/cdrom\/nocloud\//' iso-extract/boot/grub/grub.cfg
sed -i.bak 's/quiet splash/quiet splash autoinstall ds=nocloud;s=\/cdrom\/nocloud\//' iso-extract/isolinux/txt.cfg

# Create new ISO
echo "Building custom ISO..."
xorriso -as mkisofs \
  -r -V "MiniCLOUD Server AutoInstall" \
  -o "$ISO_NAME" \
  -J -l -b isolinux/isolinux.bin \
  -c isolinux/boot.cat \
  -no-emul-boot \
  -boot-load-size 4 \
  -boot-info-table \
  -eltorito-alt-boot \
  -e boot/grub/efi.img \
  -no-emul-boot \
  -append_partition 2 0xef iso-extract/boot/grub/efi.img \
  -m "isolinux/efi.img" \
  iso-extract

echo
echo "✅ Custom MiniCLOUD ISO created successfully!"
echo "📄 File: $WORK_DIR/$ISO_NAME"
echo "💾 Size: $(du -h "$ISO_NAME" | cut -f1)"
echo
echo "🔧 Usage:"
echo "1. Flash to USB: dd if=$ISO_NAME of=/dev/diskX bs=1m"
echo "2. Boot Mac Mini holding Alt/Option key"
echo "3. Select EFI Boot option"
echo "4. Installation will proceed automatically"
echo
echo "🌐 Access after installation:"
echo "• SSH: ssh daniel@[server-ip]"
echo "• Grafana: http://[server-ip]:3000 (admin/minicloud123)"
echo "• Prometheus: http://[server-ip]:9091"
echo "• Nextcloud: http://[server-ip]:8080"
echo