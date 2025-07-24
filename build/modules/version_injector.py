#!/usr/bin/env python3
"""
Module to inject version information into the build
"""

import json
import time
from pathlib import Path
from typing import Dict, Any
from utils import log_info, log_error

def inject_version_info(ctx) -> bool:
    """
    Inject version information into the Chromium build for BrowserOS
    
    Args:
        ctx: BuildContext containing version information
        
    Returns:
        bool: True if injection was successful
    """
    try:
        log_info("💉 Injecting BrowserOS version information...")
        
        # Create version info object
        version_info = {
            "browserOS_version": ctx.get_nxtscape_version(),
            "browserOS_chromium_version": ctx.get_nxtscape_chromium_version(), 
            "chromium_version": ctx.chromium_version,
            "build_date": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "architecture": ctx.architecture,
            "build_type": ctx.build_type,
            "app_name": ctx.get_app_base_name()
        }
        
        log_info(f"📝 Version info: {json.dumps(version_info, indent=2)}")
        
        # Inject into settings page JavaScript constants
        inject_settings_version_info(ctx, version_info)
        
        # Inject into about page constants
        inject_about_version_info(ctx, version_info)
        
        # Create version info header file for C++ code
        create_version_header(ctx, version_info)
        
        log_info("✅ Version information injection completed")
        return True
        
    except Exception as e:
        log_error(f"❌ Failed to inject version information: {e}")
        return False

def inject_settings_version_info(ctx, version_info: Dict[str, Any]) -> None:
    """Inject version info into settings page"""
    
    # Find the nxtscape settings TypeScript file
    settings_file = ctx.chromium_src / "chrome" / "browser" / "resources" / "settings" / "nxtscape_page" / "nxtscape_page.ts"
    
    if not settings_file.exists():
        log_error(f"Settings file not found: {settings_file}")
        return
    
    # Read the file
    content = settings_file.read_text()
    
    # Replace the version method placeholders
    replacements = {
        "return 'Loading...';": f"return '{version_info['browserOS_version']}';",
    }
    
    # Replace specific methods by function name
    if "getBrowserOSVersion_(): string {" in content:
        content = content.replace(
            "getBrowserOSVersion_(): string {\n    return 'Loading...';",
            f"getBrowserOSVersion_(): string {{\n    return '{version_info['browserOS_version']}';"
        )
    
    if "getChromiumVersion_(): string {" in content:
        content = content.replace(
            "getChromiumVersion_(): string {\n    return 'Loading...';",
            f"getChromiumVersion_(): string {{\n    return '{version_info['chromium_version']}';"
        )
    
    if "getBuildDate_(): string {" in content:
        content = content.replace(
            "getBuildDate_(): string {\n    return 'Loading...';",
            f"getBuildDate_(): string {{\n    return '{version_info['build_date']}';"
        )
    
    for old, new in replacements.items():
        if old in content:
            content = content.replace(old, new)
            log_info(f"📝 Replaced: {old[:30]}... -> {new[:30]}...")
    
    # Write back the modified content
    settings_file.write_text(content)
    log_info(f"✅ Updated settings version info: {settings_file}")

def inject_about_version_info(ctx, version_info: Dict[str, Any]) -> None:
    """Inject version info into about page"""
    
    # Find the about page TypeScript file
    about_file = ctx.chromium_src / "chrome" / "browser" / "resources" / "settings" / "about_page" / "about_page.ts"
    
    if not about_file.exists():
        log_error(f"About file not found: {about_file}")
        return
    
    # Read the file
    content = about_file.read_text()
    
    # Replace the version info object
    version_obj = f"""{{
      version: '{version_info['browserOS_version']}',
      chromiumVersion: '{version_info['chromium_version']}',
      buildDate: '{version_info['build_date']}',
      architecture: '{version_info['architecture']}',
      platform: navigator.platform,
      userAgent: navigator.userAgent,
      buildType: '{version_info['build_type']}'
    }}"""
    
    # Replace the placeholder version object
    old_pattern = """this.browserOSVersionInfo_ = {
      version: '1.0.35', // This should be dynamically loaded
      chromiumVersion: '137.0.7151.104', // This should be dynamically loaded  
      buildDate: new Date().toLocaleDateString(),
      architecture: this.getArchitecture_(),
      platform: navigator.platform,
      userAgent: navigator.userAgent,
    };"""
    
    new_pattern = f"this.browserOSVersionInfo_ = {version_obj};"
    
    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        log_info("📝 Replaced about page version info")
    
    # Write back the modified content
    about_file.write_text(content)
    log_info(f"✅ Updated about page version info: {about_file}")

def create_version_header(ctx, version_info: Dict[str, Any]) -> None:
    """Create a C++ header file with version constants"""
    
    # Create the header file path
    header_file = ctx.chromium_src / "chrome" / "common" / "browseros_version.h"
    header_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate header content
    header_content = f'''// Copyright 2024 BrowserOS Authors
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

// This file is auto-generated by the BrowserOS build system
// Do not edit manually

#ifndef CHROME_COMMON_BROWSEROS_VERSION_H_
#define CHROME_COMMON_BROWSEROS_VERSION_H_

namespace browseros {{

// Version information
constexpr char kBrowserOSVersion[] = "{version_info['browserOS_version']}";
constexpr char kBrowserOSChromiumVersion[] = "{version_info['browserOS_chromium_version']}";
constexpr char kChromiumVersion[] = "{version_info['chromium_version']}";
constexpr char kBuildDate[] = "{version_info['build_date']}";
constexpr char kArchitecture[] = "{version_info['architecture']}";
constexpr char kBuildType[] = "{version_info['build_type']}";
constexpr char kAppName[] = "{version_info['app_name']}";

}}  // namespace browseros

#endif  // CHROME_COMMON_BROWSEROS_VERSION_H_
'''
    
    # Write the header file
    header_file.write_text(header_content)
    log_info(f"✅ Created version header: {header_file}")