#!/usr/bin/swift
//
// MiniCloud Monitor Widget for macOS
// A simple Swift script that creates a menu bar app to monitor miniCLOUD
// Compatible with current macOS widget system
//

import Cocoa
import Foundation

// MARK: - Prometheus API Client
class PrometheusClient {
    let baseURL = "http://192.168.1.93:9091"
    
    struct Metrics {
        let cpuUsage: Double
        let memoryUsage: Double
        let diskUsage: Double
        let uptime: String
        let dockerContainers: Int
    }
    
    func fetchMetrics(completion: @escaping (Metrics?) -> Void) {
        // Fetch CPU usage
        let cpuQuery = "100 - (avg(rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)"
        let memQuery = "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100"
        let diskQuery = "(node_filesystem_size_bytes{mountpoint=\"/\"} - node_filesystem_avail_bytes{mountpoint=\"/\"}) / node_filesystem_size_bytes{mountpoint=\"/\"} * 100"
        
        // Simplified for demo - in production, make actual API calls
        let mockMetrics = Metrics(
            cpuUsage: Double.random(in: 10...50),
            memoryUsage: Double.random(in: 30...70),
            diskUsage: Double.random(in: 5...40),
            uptime: "9h 48m",
            dockerContainers: 4
        )
        
        completion(mockMetrics)
    }
}

// MARK: - Menu Bar App
class MiniCloudMonitor: NSObject {
    let statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
    let prometheusClient = PrometheusClient()
    var timer: Timer?
    
    override init() {
        super.init()
        setupMenuBar()
        startMonitoring()
    }
    
    func setupMenuBar() {
        if let button = statusItem.button {
            button.title = "☁️"
            button.target = self
            button.action = #selector(showMenu)
        }
    }
    
    @objc func showMenu() {
        let menu = NSMenu()
        
        // Title
        let titleItem = NSMenuItem(title: "🖥️ MiniCLOUD Monitor", action: nil, keyEquivalent: "")
        titleItem.isEnabled = false
        menu.addItem(titleItem)
        menu.addItem(NSMenuItem.separator())
        
        // Fetch and display metrics
        prometheusClient.fetchMetrics { metrics in
            DispatchQueue.main.async {
                if let metrics = metrics {
                    // CPU
                    let cpuItem = NSMenuItem(title: String(format: "CPU: %.1f%%", metrics.cpuUsage), action: nil, keyEquivalent: "")
                    menu.addItem(cpuItem)
                    
                    // Memory
                    let memItem = NSMenuItem(title: String(format: "Memory: %.1f%%", metrics.memoryUsage), action: nil, keyEquivalent: "")
                    menu.addItem(memItem)
                    
                    // Disk
                    let diskItem = NSMenuItem(title: String(format: "Disk: %.1f%%", metrics.diskUsage), action: nil, keyEquivalent: "")
                    menu.addItem(diskItem)
                    
                    // Uptime
                    let uptimeItem = NSMenuItem(title: "Uptime: \(metrics.uptime)", action: nil, keyEquivalent: "")
                    menu.addItem(uptimeItem)
                    
                    // Docker containers
                    let dockerItem = NSMenuItem(title: "Containers: \(metrics.dockerContainers) running", action: nil, keyEquivalent: "")
                    menu.addItem(dockerItem)
                    
                    menu.addItem(NSMenuItem.separator())
                }
                
                // Links
                let grafanaItem = NSMenuItem(title: "📊 Open Grafana", action: #selector(self.openGrafana), keyEquivalent: "g")
                grafanaItem.target = self
                menu.addItem(grafanaItem)
                
                let nextcloudItem = NSMenuItem(title: "☁️ Open Nextcloud", action: #selector(self.openNextcloud), keyEquivalent: "n")
                nextcloudItem.target = self
                menu.addItem(nextcloudItem)
                
                menu.addItem(NSMenuItem.separator())
                
                // Refresh
                let refreshItem = NSMenuItem(title: "🔄 Refresh", action: #selector(self.refresh), keyEquivalent: "r")
                refreshItem.target = self
                menu.addItem(refreshItem)
                
                // Quit
                let quitItem = NSMenuItem(title: "Quit", action: #selector(self.quit), keyEquivalent: "q")
                quitItem.target = self
                menu.addItem(quitItem)
                
                self.statusItem.menu = menu
                self.statusItem.button?.performClick(nil)
            }
        }
    }
    
    func startMonitoring() {
        timer = Timer.scheduledTimer(withTimeInterval: 30, repeats: true) { _ in
            self.updateStatus()
        }
        updateStatus()
    }
    
    func updateStatus() {
        prometheusClient.fetchMetrics { metrics in
            DispatchQueue.main.async {
                if let metrics = metrics {
                    if let button = self.statusItem.button {
                        if metrics.cpuUsage > 80 {
                            button.title = "☁️⚠️"
                        } else {
                            button.title = "☁️✅"
                        }
                    }
                }
            }
        }
    }
    
    @objc func openGrafana() {
        if let url = URL(string: "http://192.168.1.93:3000") {
            NSWorkspace.shared.open(url)
        }
    }
    
    @objc func openNextcloud() {
        if let url = URL(string: "http://192.168.1.93:8080") {
            NSWorkspace.shared.open(url)
        }
    }
    
    @objc func refresh() {
        updateStatus()
    }
    
    @objc func quit() {
        NSApplication.shared.terminate(nil)
    }
}

// MARK: - App Delegate
class AppDelegate: NSObject, NSApplicationDelegate {
    var monitor: MiniCloudMonitor?
    
    func applicationDidFinishLaunching(_ notification: Notification) {
        monitor = MiniCloudMonitor()
    }
}

// MARK: - Main
let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.run()