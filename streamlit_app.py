import os
from datetime import date
from html import escape
from textwrap import dedent
from typing import Any

import altair as alt
import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

from app.db.database import SessionLocal
from app.repositories.benchmark_repository import get_recent_benchmark_runs
from app.repositories.dashboard_repository import (
    get_filter_options,
    get_filtered_logs,
    get_log_detail,
)

load_dotenv()

FASTAPI_BASE_URL = os.getenv("FASTAPI_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

DEMO_ADMIN_USERNAME = os.getenv("DEMO_ADMIN_USERNAME", "admin")
DEMO_ADMIN_PASSWORD = os.getenv("DEMO_ADMIN_PASSWORD", "admin123")
DEMO_ANALYST_USERNAME = os.getenv("DEMO_ANALYST_USERNAME", "analyst")
DEMO_ANALYST_PASSWORD = os.getenv("DEMO_ANALYST_PASSWORD", "analyst123")

st.set_page_config(
    page_title="ClaudeOps Flow Dashboard",
    page_icon="🤖",
    layout="wide",
)


def inject_custom_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #f4f7fb;
            --surface: #ffffff;
            --surface-soft: #f8fafc;
            --border: #e2e8f0;
            --border-strong: #cbd5e1;

            --text: #07112f;
            --text-soft: #334155;
            --muted: #64748b;
            --muted-light: #94a3b8;

            --orange: #ff4f16;
            --orange-dark: #c2410c;
            --orange-soft: #fff4ed;
            --orange-border: #fed7aa;

            --blue: #2563eb;
            --blue-soft: #eff6ff;
            --blue-border: #bfdbfe;

            --green: #16a34a;
            --green-soft: #ecfdf5;
            --green-border: #bbf7d0;

            --red: #dc2626;
            --red-soft: #fef2f2;
            --red-border: #fecaca;

            --purple: #7c3aed;
            --purple-soft: #f5f3ff;
            --purple-border: #ddd6fe;

            --amber: #d97706;
            --amber-soft: #fffbeb;
            --amber-border: #fde68a;

            --radius-sm: 10px;
            --radius-md: 14px;
            --radius-lg: 18px;
            --radius-xl: 24px;
            --radius-2xl: 30px;

            --shadow-xs: 0 1px 2px rgba(15, 23, 42, 0.04);
            --shadow-sm: 0 8px 24px rgba(15, 23, 42, 0.06);
            --shadow-md: 0 18px 45px rgba(15, 23, 42, 0.10);
        }

        html, body, [class*="css"] {
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        html {
            scroll-behavior: smooth;
        }

        body {
            background: var(--bg);
        }

        .stApp {
            background:
                radial-gradient(circle at top right, rgba(255, 79, 22, 0.04), transparent 32%),
                linear-gradient(180deg, #ffffff 0%, var(--bg) 18%, var(--bg) 100%);
            color: var(--text);
        }

        /* Remove Streamlit top clutter / blank top spacing */
        #MainMenu {
            visibility: hidden;
        }

        footer {
            visibility: hidden;
        }

        header[data-testid="stHeader"] {
            background: transparent;
            height: 0rem;
        }

        div[data-testid="stToolbar"] {
            visibility: hidden;
            height: 0;
            position: fixed;
        }

        div[data-testid="stDecoration"] {
            display: none;
        }

        /* Main content alignment */
        .main .block-container {
            max-width: 1210px;
            padding-top: 0.25rem;
            padding-left: 1.65rem;
            padding-right: 1.65rem;
            padding-bottom: 2.25rem;
        }

        @media (min-width: 1200px) {
            .main .block-container {
                max-width: 1210px;
            }
        }

        /* Slim sidebar */
        section[data-testid="stSidebar"] {
            width: 230px !important;
            min-width: 230px !important;
            max-width: 230px !important;
            background:
                linear-gradient(180deg, #f8fafc 0%, #eef3f9 100%);
            border-right: 1px solid #dde5ef;
            box-shadow: 8px 0 30px rgba(15, 23, 42, 0.035);
        }

        section[data-testid="stSidebar"] > div {
            padding: 1.25rem 0.9rem 2rem 0.9rem;
        }

        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {
            color: var(--text);
            font-weight: 900;
            letter-spacing: -0.03em;
        }

        section[data-testid="stSidebar"] h2 {
            font-size: 1.05rem;
            margin-top: 0.4rem;
        }

        section[data-testid="stSidebar"] label {
            font-size: 0.72rem !important;
            font-weight: 800 !important;
            color: #475569 !important;
        }

        section[data-testid="stSidebar"] .stSelectbox,
        section[data-testid="stSidebar"] .stTextInput {
            margin-bottom: 0.7rem;
        }

        section[data-testid="stSidebar"] div[data-baseweb="select"],
        section[data-testid="stSidebar"] div[data-baseweb="input"] {
            border-radius: 12px !important;
            border-color: #dbe3ef !important;
            background: white !important;
            min-height: 42px;
        }

        section[data-testid="stSidebar"] input {
            font-size: 0.82rem !important;
        }

        .sidebar-brand {
            display: flex;
            align-items: center;
            gap: 9px;
            margin-bottom: 1.8rem;
        }

        .brand-mark {
            width: 28px;
            height: 28px;
            border-radius: 10px;
            background:
                radial-gradient(circle at 30% 30%, #ffffff 0 12%, transparent 13%),
                conic-gradient(from 30deg, #ff4f16, #fb923c, #ff4f16, #f97316);
            box-shadow: 0 8px 18px rgba(249, 115, 22, 0.25);
        }

        .brand-name {
            font-size: 0.98rem;
            font-weight: 950;
            letter-spacing: -0.04em;
            color: var(--text);
        }

        .sidebar-section-label {
            margin-top: 1.3rem;
            margin-bottom: 0.7rem;
            font-size: 0.72rem;
            color: #64748b;
            font-weight: 900;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .sidebar-user-line {
            display: flex;
            align-items: center;
            gap: 9px;
            color: #0f172a;
            font-size: 0.82rem;
            font-weight: 750;
            margin-bottom: 0.65rem;
        }

        .sidebar-icon {
            width: 24px;
            height: 24px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 9px;
            color: #1e40af;
            background: #eff6ff;
            border: 1px solid #dbeafe;
        }

        .sidebar-divider {
            height: 1px;
            background: #dbe3ef;
            margin: 1.25rem 0;
        }

        .sidebar-role-pill {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            padding: 6px 10px;
            border-radius: 999px;
            background: #ffffff;
            border: 1px solid #dbe3ef;
            color: #334155;
            font-size: 0.73rem;
            font-weight: 850;
            box-shadow: var(--shadow-xs);
        }

        .sidebar-dot {
            height: 7px;
            width: 7px;
            background: #22c55e;
            border-radius: 999px;
            display: inline-block;
            box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.13);
        }

        /* Hero */
        .hero-card {
            position: relative;
            overflow: hidden;
            background:
                radial-gradient(circle at 92% 35%, rgba(255, 79, 22, 0.72), transparent 30%),
                radial-gradient(circle at 70% 110%, rgba(249, 115, 22, 0.35), transparent 42%),
                linear-gradient(135deg, #071125 0%, #101a35 48%, #321d2b 72%, #8b2f12 130%);
            border-radius: 22px;
            padding: 30px 34px;
            color: white;
            margin-bottom: 1rem;
            box-shadow: 0 22px 54px rgba(15, 23, 42, 0.18);
            border: 1px solid rgba(255, 255, 255, 0.12);
        }

        .hero-card::before {
            content: "";
            position: absolute;
            right: -90px;
            top: -25px;
            width: 520px;
            height: 330px;
            opacity: 0.5;
            background:
                repeating-radial-gradient(ellipse at center, rgba(255, 139, 61, 0.45) 0 1px, transparent 1px 14px);
            transform: rotate(-11deg);
        }

        .hero-card::after {
            content: "";
            position: absolute;
            right: -80px;
            bottom: -110px;
            width: 620px;
            height: 260px;
            opacity: 0.42;
            background:
                linear-gradient(130deg, transparent 0 35%, rgba(255, 113, 36, 0.22) 36%, transparent 38%),
                linear-gradient(150deg, transparent 0 42%, rgba(255, 113, 36, 0.28) 43%, transparent 45%),
                linear-gradient(165deg, transparent 0 50%, rgba(255, 113, 36, 0.24) 51%, transparent 53%);
        }

        .hero-inner {
            position: relative;
            z-index: 1;
        }

        .hero-title {
            font-size: 2rem;
            font-weight: 950;
            margin-bottom: 0.45rem;
            line-height: 1.06;
            letter-spacing: -0.055em;
        }

        .hero-subtitle {
            font-size: 0.95rem;
            opacity: 0.94;
            line-height: 1.55;
            max-width: 850px;
        }

        .chip-row {
            margin-top: 18px;
            display: flex;
            flex-wrap: wrap;
            gap: 9px;
        }

        .chip {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            padding: 8px 13px;
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.12);
            border: 1px solid rgba(255, 255, 255, 0.22);
            font-size: 0.78rem;
            font-weight: 850;
            color: #f8fafc;
            backdrop-filter: blur(6px);
        }

        .top-note {
            display: grid;
            grid-template-columns: 54px 1fr;
            gap: 16px;
            align-items: center;
            background:
                radial-gradient(circle at left, rgba(249, 115, 22, 0.08), transparent 32%),
                linear-gradient(135deg, #fffaf5 0%, #ffffff 100%);
            border: 1px solid var(--orange-border);
            border-left: 4px solid #fb923c;
            border-radius: 18px;
            padding: 20px 22px;
            margin-bottom: 1.05rem;
            box-shadow: var(--shadow-xs);
        }

        .top-note-icon {
            width: 48px;
            height: 48px;
            border-radius: 999px;
            background: #ffedd5;
            color: var(--orange);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            font-weight: 950;
            border: 1px solid #fed7aa;
        }

        .top-note-title {
            font-size: 0.95rem;
            font-weight: 950;
            color: #c2410c;
            margin-bottom: 0.35rem;
            letter-spacing: -0.02em;
        }

        .top-note-text {
            color: #334155;
            font-size: 0.92rem;
            line-height: 1.6;
        }

        /* Section headings */
        .section-title {
            font-size: 1.38rem;
            font-weight: 950;
            margin: 1.25rem 0 0.28rem 0;
            color: var(--text);
            letter-spacing: -0.045em;
        }

        .section-subtitle {
            color: var(--muted);
            font-size: 0.9rem;
            margin-bottom: 0.95rem;
            line-height: 1.55;
        }

        .section-kicker {
            color: var(--orange);
            text-transform: uppercase;
            font-size: 0.72rem;
            letter-spacing: 0.08em;
            font-weight: 950;
            margin-bottom: 0.2rem;
        }

        /* Cards */
        .kpi-card {
            position: relative;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 18px 18px 15px 18px;
            box-shadow: var(--shadow-xs);
            min-height: 126px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
        }

        .kpi-card:hover {
            transform: translateY(-1px);
            box-shadow: var(--shadow-sm);
            border-color: #d4ddea;
        }

        .kpi-card-header {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 12px;
        }

        .kpi-icon {
            width: 38px;
            height: 38px;
            border-radius: 13px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 1.1rem;
            font-weight: 900;
            flex: 0 0 auto;
        }

        .icon-blue {
            color: var(--blue);
            background: var(--blue-soft);
            border: 1px solid var(--blue-border);
        }

        .icon-green {
            color: var(--green);
            background: var(--green-soft);
            border: 1px solid var(--green-border);
        }

        .icon-orange {
            color: var(--orange);
            background: var(--orange-soft);
            border: 1px solid var(--orange-border);
        }

        .icon-red {
            color: var(--red);
            background: var(--red-soft);
            border: 1px solid var(--red-border);
        }

        .icon-purple {
            color: var(--purple);
            background: var(--purple-soft);
            border: 1px solid var(--purple-border);
        }

        .icon-amber {
            color: var(--amber);
            background: var(--amber-soft);
            border: 1px solid var(--amber-border);
        }

        .icon-cyan {
            color: #0891b2;
            background: #ecfeff;
            border: 1px solid #a5f3fc;
        }
        
        .kpi-label {
            color: var(--muted);
            font-size: 0.68rem;
            font-weight: 950;
            text-transform: uppercase;
            letter-spacing: 0.075em;
        }

        .kpi-value {
            color: var(--text);
            font-size: 1.55rem;
            font-weight: 950;
            margin-top: 8px;
            margin-bottom: 5px;
            line-height: 1.08;
            letter-spacing: -0.045em;
            word-break: break-word;
        }

        .kpi-card.compact {
            min-height: 112px !important;
        }

        .kpi-value.compact {
            font-size: 1.18rem !important;
            line-height: 1.22 !important;
        }

        .kpi-sub {
            color: var(--muted);
            font-size: 0.78rem;
            line-height: 1.45;
        }

        .info-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 18px;
            box-shadow: var(--shadow-xs);
            margin-bottom: 0.85rem;
            min-height: 112px;
        }

        .info-card-title {
            font-size: 0.95rem;
            font-weight: 950;
            color: var(--text);
            margin-bottom: 0.48rem;
            letter-spacing: -0.025em;
        }

        .info-card-text {
            color: #475569;
            font-size: 0.88rem;
            line-height: 1.6;
        }

        .panel-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 18px;
            box-shadow: var(--shadow-xs);
            margin-bottom: 0.95rem;
        }

        /* Badges */
        .badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 10px;
            border-radius: 999px;
            font-size: 0.72rem;
            font-weight: 900;
            margin-right: 6px;
            margin-bottom: 7px;
            border: 1px solid transparent;
            white-space: nowrap;
        }

        .badge-neutral {
            background: var(--blue-soft);
            color: #1d4ed8;
            border-color: var(--blue-border);
        }

        .badge-success {
            background: var(--green-soft);
            color: #047857;
            border-color: var(--green-border);
        }

        .badge-warning {
            background: var(--amber-soft);
            color: #b45309;
            border-color: var(--amber-border);
        }

        .badge-danger {
            background: var(--red-soft);
            color: #b91c1c;
            border-color: var(--red-border);
        }

        .badge-dark {
            background: #f1f5f9;
            color: #0f172a;
            border-color: #e2e8f0;
        }

        .badge-purple {
            background: var(--purple-soft);
            color: #6d28d9;
            border-color: var(--purple-border);
        }

        /* Mini stat cards */
        .mini-stat {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 15px;
            margin-bottom: 10px;
            box-shadow: var(--shadow-xs);
            min-height: 86px;
        }

        .mini-stat-label {
            color: var(--muted);
            font-size: 0.68rem;
            font-weight: 950;
            text-transform: uppercase;
            letter-spacing: 0.075em;
        }

        .mini-stat-value {
            color: var(--text);
            font-size: 1.05rem;
            font-weight: 950;
            margin-top: 7px;
            line-height: 1.2;
            word-break: break-word;
        }

        .approval-stat {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 14px 15px;
            min-height: 84px;
            box-shadow: var(--shadow-xs);
        }

        .approval-stat-label {
            color: var(--muted);
            font-size: 0.68rem;
            font-weight: 950;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            margin-bottom: 7px;
        }

        .approval-stat-value {
            color: var(--text);
            font-size: 1rem;
            font-weight: 950;
            line-height: 1.25;
            word-break: break-word;
        }

        /* Login / workspace page */
        .login-screen {
            max-width: 1280px;
            margin: 1.2rem auto 0 auto;
        }

        .login-grid {
            display: grid;
            grid-template-columns: 1.05fr 0.95fr;
            gap: 28px;
            align-items: stretch;
        }

        .login-marketing-panel {
            min-height: 660px;
            border-radius: 32px;
            padding: 42px;
            color: #ffffff;
            position: relative;
            overflow: hidden;
            background:
                radial-gradient(circle at 80% 85%, rgba(255, 79, 22, 0.42), transparent 34%),
                radial-gradient(circle at 15% 20%, rgba(37, 99, 235, 0.30), transparent 26%),
                linear-gradient(135deg, #061027 0%, #11164a 48%, #271a55 72%, #6b2415 120%);
            box-shadow: 0 26px 70px rgba(15, 23, 42, 0.22);
            border: 1px solid rgba(255,255,255,0.12);
        }

        .login-marketing-panel::after {
            content: "";
            position: absolute;
            left: -90px;
            bottom: -120px;
            width: 720px;
            height: 320px;
            opacity: 0.32;
            background:
                repeating-radial-gradient(ellipse at center, rgba(96, 165, 250, 0.36) 0 1px, transparent 1px 15px);
            transform: rotate(-8deg);
        }

        .login-brand-row {
            display: flex;
            align-items: center;
            gap: 14px;
            position: relative;
            z-index: 1;
            margin-bottom: 70px;
        }

        .login-brand-mark {
            width: 42px;
            height: 42px;
            border-radius: 16px;
            background:
                radial-gradient(circle at 30% 30%, #ffffff 0 9%, transparent 10%),
                conic-gradient(from 40deg, #2563eb, #8b5cf6, #fb7185, #fb923c, #2563eb);
            box-shadow: 0 16px 34px rgba(96, 165, 250, 0.28);
        }

        .login-brand-name {
            font-size: 1.45rem;
            font-weight: 950;
            letter-spacing: -0.05em;
        }

        .login-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 16px;
            border-radius: 999px;
            background: rgba(255,255,255,0.10);
            border: 1px solid rgba(255,255,255,0.16);
            color: #93c5fd;
            font-size: 0.78rem;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            position: relative;
            z-index: 1;
            margin-bottom: 28px;
        }

        .login-main-title {
            position: relative;
            z-index: 1;
            font-size: 3.45rem;
            line-height: 1.1;
            font-weight: 950;
            letter-spacing: -0.065em;
            max-width: 640px;
            margin-bottom: 22px;
        }

        .login-gradient-word {
            background: linear-gradient(90deg, #8b5cf6 0%, #fb7185 45%, #fb923c 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .login-main-copy {
            position: relative;
            z-index: 1;
            max-width: 600px;
            color: rgba(255,255,255,0.78);
            font-size: 1.05rem;
            line-height: 1.65;
            margin-bottom: 34px;
        }

        .login-feature-grid {
            position: relative;
            z-index: 1;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 14px;
            margin-top: 24px;
        }

        .login-feature-card {
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.14);
            border-radius: 18px;
            padding: 18px;
            display: grid;
            grid-template-columns: 44px 1fr;
            gap: 14px;
            align-items: center;
            backdrop-filter: blur(8px);
        }

        .login-feature-icon {
            width: 44px;
            height: 44px;
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            background: rgba(37, 99, 235, 0.32);
            border: 1px solid rgba(147, 197, 253, 0.25);
        }

        .login-feature-title {
            font-size: 0.96rem;
            font-weight: 950;
            margin-bottom: 4px;
        }

        .login-feature-text {
            color: rgba(255,255,255,0.68);
            font-size: 0.82rem;
            line-height: 1.45;
        }

        .login-security-note {
            position: absolute;
            left: 42px;
            bottom: 30px;
            z-index: 1;
            color: rgba(255,255,255,0.72);
            font-size: 0.85rem;
            display: flex;
            align-items: center;
            gap: 9px;
        }

        .workspace-panel {
            min-height: 660px;
            border-radius: 32px;
            padding: 38px;
            background:
                radial-gradient(circle at 50% 0%, rgba(37, 99, 235, 0.06), transparent 35%),
                #ffffff;
            border: 1px solid #dbe3ef;
            box-shadow: 0 26px 70px rgba(15, 23, 42, 0.12);
        }

        .workspace-title {
            font-size: 1.85rem;
            font-weight: 950;
            letter-spacing: -0.05em;
            color: var(--text);
            text-align: center;
            margin-bottom: 8px;
        }

        .workspace-subtitle {
            color: var(--muted);
            text-align: center;
            font-size: 0.95rem;
            margin-bottom: 26px;
        }

        .workspace-card-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-bottom: 18px;
        }

        .workspace-option-card {
            min-height: 190px;
            border-radius: 20px;
            border: 1px solid #dbe3ef;
            background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
            padding: 22px 18px;
            text-align: center;
            position: relative;
            box-shadow: var(--shadow-xs);
        }

        .workspace-option-card.selected {
            border-color: #93b4ff;
            box-shadow: 0 16px 40px rgba(37, 99, 235, 0.14);
            background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%);
        }

        .workspace-check {
            position: absolute;
            top: 14px;
            right: 14px;
            width: 24px;
            height: 24px;
            border-radius: 999px;
            background: #2563eb;
            color: white;
            font-size: 0.8rem;
            font-weight: 900;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .workspace-icon {
            width: 64px;
            height: 64px;
            border-radius: 999px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 6px auto 16px auto;
            font-size: 1.8rem;
            border: 1px solid;
        }

        .workspace-icon.admin {
            background: #eff6ff;
            color: #2563eb;
            border-color: #bfdbfe;
        }

        .workspace-icon.analyst {
            background: #fff7ed;
            color: #f97316;
            border-color: #fed7aa;
        }

        .workspace-card-title {
            color: var(--text);
            font-weight: 950;
            font-size: 1rem;
            margin-bottom: 8px;
        }

        .workspace-card-text {
            color: var(--muted);
            font-size: 0.86rem;
            line-height: 1.55;
        }

        .login-divider-label {
            display: flex;
            align-items: center;
            gap: 14px;
            color: var(--muted);
            font-size: 0.86rem;
            margin: 22px 0 18px 0;
        }

        .login-divider-label::before,
        .login-divider-label::after {
            content: "";
            height: 1px;
            background: #e2e8f0;
            flex: 1;
        }

        .login-form-caption {
            font-size: 0.86rem;
            color: var(--muted);
            margin-bottom: 14px;
            text-align: center;
        }

        .login-footer-text {
            text-align: center;
            color: var(--muted);
            font-size: 0.78rem;
            margin-top: 18px;
        }

        @media (max-width: 980px) {
            .login-grid {
                grid-template-columns: 1fr;
            }

            .login-marketing-panel,
            .workspace-panel {
                min-height: auto;
            }

            .login-main-title {
                font-size: 2.4rem;
            }

            .login-feature-grid,
            .workspace-card-row {
                grid-template-columns: 1fr;
            }

            .login-security-note {
                position: relative;
                left: auto;
                bottom: auto;
                margin-top: 28px;
            }
        }

        /* Observability */
        .obs-section-card {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 22px;
            padding: 20px;
            box-shadow: var(--shadow-sm);
            margin-bottom: 18px;
        }

        .obs-section-top {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 16px;
            margin-bottom: 14px;
            flex-wrap: wrap;
        }

        .obs-section-title {
            color: var(--text);
            font-size: 1rem;
            font-weight: 950;
            letter-spacing: -0.025em;
            margin-bottom: 4px;
        }

        .obs-section-text {
            color: var(--muted);
            font-size: 0.86rem;
            line-height: 1.55;
        }

        .obs-window-pill {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            background: #fff7ed;
            color: #c2410c;
            border: 1px solid #fed7aa;
            border-radius: 999px;
            padding: 7px 11px;
            font-size: 0.78rem;
            font-weight: 900;
        }

        .obs-alert-list {
            display: grid;
            gap: 10px;
            margin-top: 8px;
        }

        .obs-alert-item {
            display: grid;
            grid-template-columns: 38px 1fr;
            gap: 12px;
            align-items: flex-start;
            border-radius: 15px;
            padding: 13px 14px;
            border: 1px solid transparent;
        }

        .obs-alert-icon {
            width: 32px;
            height: 32px;
            border-radius: 11px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 950;
        }

        .obs-alert-high {
            background: #fef2f2;
            border-color: #fecaca;
            color: #991b1b;
        }

        .obs-alert-high .obs-alert-icon {
            background: #fee2e2;
            color: #dc2626;
        }

        .obs-alert-medium {
            background: #fffbeb;
            border-color: #fde68a;
            color: #92400e;
        }

        .obs-alert-medium .obs-alert-icon {
            background: #fef3c7;
            color: #d97706;
        }

        .obs-alert-low {
            background: #eff6ff;
            border-color: #bfdbfe;
            color: #1e40af;
        }

        .obs-alert-low .obs-alert-icon {
            background: #dbeafe;
            color: #2563eb;
        }

        .obs-alert-title {
            font-size: 0.78rem;
            font-weight: 950;
            text-transform: uppercase;
            letter-spacing: 0.065em;
            margin-bottom: 3px;
        }

        .obs-alert-message {
            font-size: 0.9rem;
            line-height: 1.5;
        }

        .correction-form-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 20px;
            box-shadow: var(--shadow-sm);
            margin-bottom: 18px;
        }

        .raw-prediction-card {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 18px;
            padding: 16px;
            margin-bottom: 16px;
        }

        .raw-prediction-title {
            color: var(--text);
            font-size: 0.95rem;
            font-weight: 950;
            margin-bottom: 10px;
        }

        .audit-table-note {
            color: var(--muted);
            font-size: 0.84rem;
            line-height: 1.5;
            margin: 4px 0 12px 0;
        }

        /* Integrations & Benchmark */
        .integration-status-card {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 18px;
            box-shadow: var(--shadow-sm);
            min-height: 132px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .integration-status-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 14px;
        }

        .integration-status-label {
            color: var(--muted);
            font-size: 0.72rem;
            font-weight: 950;
            text-transform: uppercase;
            letter-spacing: 0.075em;
        }

        .integration-status-value {
            color: var(--text);
            font-size: 1.25rem;
            font-weight: 950;
            letter-spacing: -0.04em;
            margin-bottom: 6px;
        }

        .integration-status-sub {
            color: var(--muted);
            font-size: 0.82rem;
            line-height: 1.45;
        }

        .integration-status-icon {
            width: 38px;
            height: 38px;
            border-radius: 13px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 950;
            border: 1px solid transparent;
        }

        .integration-contract-card {
            background:
                radial-gradient(circle at top right, rgba(37, 99, 235, 0.07), transparent 35%),
                linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 20px;
            box-shadow: var(--shadow-sm);
            margin-bottom: 16px;
        }

        .integration-contract-title {
            font-size: 1rem;
            font-weight: 950;
            color: var(--text);
            letter-spacing: -0.025em;
            margin-bottom: 6px;
        }

        .integration-contract-text {
            color: var(--muted);
            font-size: 0.88rem;
            line-height: 1.55;
            margin-bottom: 14px;
        }

        .benchmark-control-card {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 20px;
            box-shadow: var(--shadow-sm);
            margin-bottom: 18px;
        }

        .benchmark-control-title {
            font-size: 1rem;
            font-weight: 950;
            color: var(--text);
            margin-bottom: 4px;
            letter-spacing: -0.025em;
        }

        .benchmark-control-text {
            color: var(--muted);
            font-size: 0.86rem;
            line-height: 1.5;
            margin-bottom: 14px;
        }

        .benchmark-table-note {
            color: var(--muted);
            font-size: 0.84rem;
            line-height: 1.5;
            margin: 4px 0 12px 0;
        }

        .history-chart-card {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 18px;
            box-shadow: var(--shadow-sm);
            margin-bottom: 16px;
        }

        /* Approval Queue */
        .approval-card {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 22px;
            padding: 22px;
            box-shadow: var(--shadow-sm);
            margin-bottom: 18px;
        }

        .approval-card-top {
            display: grid;
            grid-template-columns: 1.6fr 0.9fr;
            gap: 18px;
            align-items: flex-start;
            margin-bottom: 16px;
        }

        .approval-title {
            font-size: 1.15rem;
            font-weight: 950;
            color: var(--text);
            letter-spacing: -0.035em;
            margin-bottom: 8px;
            line-height: 1.25;
        }

        .approval-summary {
            color: #475569;
            font-size: 0.9rem;
            line-height: 1.58;
            max-width: 760px;
        }

        .approval-badge-area {
            text-align: right;
        }

        .approval-stat-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin: 14px 0;
        }

        .approval-reason-box {
            display: grid;
            grid-template-columns: 38px 1fr;
            gap: 12px;
            align-items: flex-start;
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            border-left: 4px solid #2563eb;
            border-radius: 16px;
            padding: 14px 16px;
            margin: 14px 0;
        }

        .approval-reason-icon {
            width: 32px;
            height: 32px;
            border-radius: 11px;
            background: #dbeafe;
            color: #1d4ed8;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 950;
        }

        .approval-reason-title {
            font-size: 0.78rem;
            color: #1d4ed8;
            font-weight: 950;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            margin-bottom: 4px;
        }

        .approval-reason-text {
            color: #1e3a8a;
            font-size: 0.9rem;
            line-height: 1.55;
        }

        .approval-request-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            flex-wrap: wrap;
            margin: 16px 0 14px 0;
        }

        .approval-request-id {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            color: #475569;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 999px;
            padding: 7px 11px;
            font-size: 0.78rem;
            font-weight: 800;
        }

        .approval-created-at {
            color: var(--muted);
            font-size: 0.78rem;
            font-weight: 700;
        }

        .approval-action-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-top: 12px;
        }

        .policy-result-card {
            background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 18px;
            box-shadow: var(--shadow-xs);
            margin-bottom: 16px;
        }

        .policy-result-title {
            font-size: 0.98rem;
            font-weight: 950;
            color: var(--text);
            margin-bottom: 6px;
        }

        .policy-result-text {
            color: var(--muted);
            font-size: 0.88rem;
            line-height: 1.55;
            margin-bottom: 12px;
        }

        @media (max-width: 900px) {
            .approval-card-top,
            .approval-stat-grid,
            .approval-action-row {
                grid-template-columns: 1fr;
            }

            .approval-badge-area {
                text-align: left;
            }
        }

        /* Operations Dashboard */
        .chart-panel {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 18px 18px 12px 18px;
            box-shadow: var(--shadow-sm);
            margin-bottom: 16px;
            min-height: 360px;
        }

        .chart-panel-title {
            font-size: 0.98rem;
            font-weight: 950;
            color: var(--text);
            letter-spacing: -0.02em;
            margin-bottom: 4px;
        }

        .chart-panel-subtitle {
            color: var(--muted);
            font-size: 0.84rem;
            line-height: 1.45;
            margin-bottom: 14px;
        }

        .table-action-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            margin: 6px 0 12px 0;
            flex-wrap: wrap;
        }

        .table-meta-text {
            color: var(--muted);
            font-size: 0.86rem;
            line-height: 1.45;
        }

        .detail-message {
            border-radius: 14px;
            padding: 14px 16px;
            margin-bottom: 10px;
            font-size: 0.92rem;
            line-height: 1.55;
            border: 1px solid transparent;
        }

        .detail-message-blue {
            background: #eff6ff;
            border-color: #bfdbfe;
            color: #1d4ed8;
        }

        .detail-message-green {
            background: #ecfdf5;
            border-color: #bbf7d0;
            color: #047857;
        }

        .detail-message-yellow {
            background: #fffbeb;
            border-color: #fde68a;
            color: #92400e;
        }

        .request-selector-label {
            color: var(--muted);
            font-size: 0.84rem;
            font-weight: 800;
            margin-top: 12px;
            margin-bottom: 6px;
        }

        /* Submit Ticket page */
        .submit-form-intro {
            margin-bottom: 14px;
        }

        .submit-form-title {
            font-size: 1.05rem;
            font-weight: 950;
            color: var(--text);
            letter-spacing: -0.025em;
            margin-bottom: 4px;
        }

        .submit-form-subtitle {
            color: var(--muted);
            font-size: 0.88rem;
            line-height: 1.55;
            margin-bottom: 10px;
        }

        .feature-card {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: var(--radius-lg);
            padding: 20px;
            box-shadow: var(--shadow-sm);
            margin-bottom: 14px;
            display: grid;
            grid-template-columns: 50px 1fr;
            gap: 16px;
            align-items: flex-start;
            min-height: 122px;
        }

        .feature-icon {
            width: 46px;
            height: 46px;
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            font-weight: 900;
            border: 1px solid transparent;
        }

        .feature-icon-blue {
            background: #eff6ff;
            color: #2563eb;
            border-color: #bfdbfe;
        }

        .feature-icon-green {
            background: #ecfdf5;
            color: #059669;
            border-color: #bbf7d0;
        }

        .feature-icon-purple {
            background: #f5f3ff;
            color: #7c3aed;
            border-color: #ddd6fe;
        }

        .feature-icon-orange {
            background: #fff7ed;
            color: #f97316;
            border-color: #fed7aa;
        }

        .feature-title {
            font-size: 0.98rem;
            font-weight: 950;
            color: var(--text);
            margin-bottom: 7px;
            letter-spacing: -0.02em;
        }

        .feature-text {
            color: #475569;
            font-size: 0.9rem;
            line-height: 1.62;
        }

        .simulation-success-card {
            background: linear-gradient(135deg, #fff7ed 0%, #ffffff 100%);
            border: 1px solid #fed7aa;
            border-radius: 16px;
            padding: 15px 16px;
            color: #9a3412;
            font-size: 0.9rem;
            line-height: 1.55;
            margin-top: 10px;
        }

        .result-callout {
            display: grid;
            grid-template-columns: 42px 1fr;
            gap: 14px;
            align-items: flex-start;
            background: #fffbeb;
            border: 1px solid #fde68a;
            border-radius: 16px;
            padding: 15px 16px;
            margin: 14px 0 16px 0;
            color: #92400e;
        }

        .result-callout-icon {
            width: 34px;
            height: 34px;
            border-radius: 12px;
            background: #fff7ed;
            border: 1px solid #fed7aa;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 950;
            color: #f97316;
        }

        .result-callout-title {
            font-weight: 950;
            margin-bottom: 3px;
            color: #92400e;
        }

        .result-callout-text {
            font-size: 0.9rem;
            line-height: 1.55;
        }

        .result-tabs-note {
            color: var(--muted);
            font-size: 0.86rem;
            margin-top: 4px;
            margin-bottom: 8px;
        }

        .result-summary-box {
            border-radius: 14px;
            padding: 14px 16px;
            margin-bottom: 10px;
            font-size: 0.93rem;
            line-height: 1.6;
            border: 1px solid transparent;
        }

        .result-summary-blue {
            background: #eff6ff;
            color: #1d4ed8;
            border-color: #bfdbfe;
        }

        .result-summary-green {
            background: #ecfdf5;
            color: #047857;
            border-color: #bbf7d0;
        }

        /* Project Overview */
        .overview-hero-panel {
            background:
                radial-gradient(circle at top right, rgba(255, 79, 22, 0.13), transparent 32%),
                linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid var(--border);
            border-radius: 22px;
            padding: 22px;
            box-shadow: var(--shadow-sm);
            margin-bottom: 18px;
        }

        .overview-hero-title {
            color: var(--text);
            font-size: 1.28rem;
            font-weight: 950;
            letter-spacing: -0.045em;
            margin-bottom: 8px;
        }

        .overview-hero-text {
            color: #475569;
            font-size: 0.92rem;
            line-height: 1.65;
            max-width: 980px;
        }

        .overview-card {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 19px;
            box-shadow: var(--shadow-sm);
            min-height: 188px;
            margin-bottom: 16px;
        }

        .overview-card-icon {
            width: 44px;
            height: 44px;
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 950;
            margin-bottom: 14px;
            border: 1px solid transparent;
        }

        .overview-card-title {
            color: var(--text);
            font-size: 0.98rem;
            font-weight: 950;
            letter-spacing: -0.025em;
            margin-bottom: 8px;
        }

        .overview-card-text {
            color: #475569;
            font-size: 0.88rem;
            line-height: 1.6;
        }

        .overview-flow-grid {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 12px;
            margin: 12px 0 20px 0;
        }

        .overview-flow-step {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 16px;
            box-shadow: var(--shadow-sm);
            min-height: 148px;
        }

        .overview-step-number {
            width: 30px;
            height: 30px;
            border-radius: 999px;
            background: var(--orange-soft);
            color: var(--orange-dark);
            border: 1px solid var(--orange-border);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 950;
            font-size: 0.8rem;
            margin-bottom: 12px;
        }

        .overview-step-title {
            color: var(--text);
            font-size: 0.88rem;
            font-weight: 950;
            margin-bottom: 6px;
        }

        .overview-step-text {
            color: var(--muted);
            font-size: 0.8rem;
            line-height: 1.5;
        }

        .role-access-card {
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 20px;
            box-shadow: var(--shadow-sm);
            margin-bottom: 16px;
        }

        .role-access-title {
            color: var(--text);
            font-size: 1rem;
            font-weight: 950;
            letter-spacing: -0.025em;
            margin-bottom: 6px;
        }

        .role-access-text {
            color: var(--muted);
            font-size: 0.88rem;
            line-height: 1.55;
            margin-bottom: 14px;
        }

        .role-pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 10px;
            margin-bottom: 16px;
        }

        .role-pill {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            padding: 7px 11px;
            border-radius: 999px;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            color: #334155;
            font-size: 0.78rem;
            font-weight: 850;
        }

        @media (max-width: 1050px) {
            .overview-flow-grid {
                grid-template-columns: 1fr 1fr;
            }
        }

        @media (max-width: 720px) {
            .overview-flow-grid {
                grid-template-columns: 1fr;
            }
        }

        /* Streamlit controls */
        .stButton > button {
            border-radius: 12px;
            border: 1px solid #cbd5e1;
            background: #ffffff;
            color: var(--text);
            font-weight: 850;
            min-height: 40px;
            transition: all 0.15s ease;
        }

        .stButton > button:hover {
            border-color: var(--orange);
            color: var(--orange);
            box-shadow: 0 8px 20px rgba(249, 115, 22, 0.12);
            transform: translateY(-1px);
        }

        .stFormSubmitButton > button {
            border-radius: 12px;
            border: 1px solid var(--orange);
            background: linear-gradient(135deg, #ff4f16 0%, #f97316 100%);
            color: #ffffff;
            font-weight: 900;
            min-height: 42px;
            box-shadow: 0 10px 24px rgba(249, 115, 22, 0.22);
        }

        .stFormSubmitButton > button:hover {
            border-color: #ea580c;
            color: #ffffff;
            box-shadow: 0 12px 28px rgba(249, 115, 22, 0.28);
        }

        .stDownloadButton > button {
            border-radius: 12px;
            font-weight: 850;
            border-color: #cbd5e1;
        }

        div[data-baseweb="input"] input,
        textarea,
        div[data-baseweb="select"] {
            border-radius: 12px !important;
        }

        div[data-baseweb="input"],
        div[data-baseweb="select"],
        textarea {
            border-color: #dbe3ef !important;
        }

        .stTextArea textarea {
            color: var(--text) !important;
            -webkit-text-fill-color: var(--text) !important;
            background: #ffffff !important;
            border-radius: 14px !important;
            line-height: 1.55 !important;
        }

        /* Tabs */
        div[data-testid="stTabs"] {
            margin-top: 0.6rem;
        }

        button[data-baseweb="tab"] {
            font-weight: 850;
            color: #475569;
            padding: 12px 10px;
            font-size: 0.84rem;
        }

        button[data-baseweb="tab"][aria-selected="true"] {
            color: var(--orange);
        }

        button[data-baseweb="tab"][aria-selected="true"] p {
            color: var(--orange);
            font-weight: 950;
        }

        div[data-baseweb="tab-highlight"] {
            background-color: var(--orange) !important;
            height: 2px !important;
        }

        /* Dataframes / tables */
        div[data-testid="stDataFrame"] {
            border-radius: 14px;
            overflow: hidden;
            border: 1px solid var(--border);
            box-shadow: var(--shadow-xs);
            background: white;
        }

        /* Alerts */
        div[data-testid="stAlert"] {
            border-radius: 14px;
            border: 1px solid rgba(148, 163, 184, 0.24);
            box-shadow: var(--shadow-xs);
        }

        /* Expanders */
        details {
            border-radius: 14px !important;
            border-color: var(--border) !important;
            background: #ffffff !important;
            box-shadow: var(--shadow-xs);
        }

        details summary {
            font-weight: 850;
            color: #334155;
        }

        /* Code / JSON */
        div[data-testid="stJson"] {
            border-radius: 14px;
        }

        pre {
            border-radius: 14px !important;
        }

        /* Charts */
        div[data-testid="stVegaLiteChart"],
        div[data-testid="stArrowVegaLiteChart"] {
            background: white;
            border-radius: 16px;
            border: 1px solid var(--border);
            box-shadow: var(--shadow-xs);
            padding: 10px;
        }

        /* Responsive */
        @media (max-width: 900px) {
            section[data-testid="stSidebar"] {
                width: 100% !important;
                max-width: 100% !important;
            }

            .main .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }

            .hero-card,
            .login-product-card {
                padding: 24px;
                border-radius: 22px;
            }

            .hero-title,
            .login-title {
                font-size: 2rem;
            }

            .kpi-value {
                font-size: 1.35rem;
            }

            .top-note {
                grid-template-columns: 1fr;
            }
        }
        
        .stApp {
            background:
                radial-gradient(circle at top right, rgba(255, 79, 22, 0.045), transparent 34%),
                linear-gradient(180deg, #ffffff 0%, #f4f7fb 20%, #eef3f9 100%) !important;
        }
        
        /* Main content width and spacing like target images */
        .main .block-container {
            max-width: 1240px !important;
            padding-top: 1.2rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            padding-bottom: 4rem !important;
        }
        
        /* Sidebar closer to generated target */
        section[data-testid="stSidebar"] {
            width: 245px !important;
            min-width: 245px !important;
            max-width: 245px !important;
            background: linear-gradient(180deg, #f8fbff 0%, #eef3f8 100%) !important;
            border-right: 1px solid #dde6f0 !important;
            box-shadow: 10px 0 34px rgba(15, 23, 42, 0.04) !important;
        }
        
        section[data-testid="stSidebar"] > div {
            padding: 2rem 1rem 2rem 1rem !important;
        }
        
        .sidebar-brand {
            margin-bottom: 2.2rem !important;
        }
        
        .brand-mark {
            width: 30px !important;
            height: 30px !important;
            border-radius: 11px !important;
            background:
                radial-gradient(circle at 32% 32%, #ffffff 0 10%, transparent 11%),
                linear-gradient(135deg, #ff4f16 0%, #fb923c 48%, #ef4444 100%) !important;
            box-shadow: 0 10px 24px rgba(249, 115, 22, 0.28) !important;
        }
        
        .brand-name {
            font-size: 1rem !important;
            font-weight: 950 !important;
        }
        
        .sidebar-section-label {
            margin-top: 1.5rem !important;
            margin-bottom: 0.85rem !important;
            font-size: 0.72rem !important;
            color: #64748b !important;
            font-weight: 950 !important;
            letter-spacing: 0.09em !important;
        }
        
        .sidebar-user-line {
            font-size: 0.82rem !important;
            font-weight: 850 !important;
            margin-bottom: 0.8rem !important;
        }
        
        .sidebar-icon {
            width: 26px !important;
            height: 26px !important;
            border-radius: 10px !important;
            background: #eff6ff !important;
            color: #2563eb !important;
        }
        
        /* Better sidebar controls */
        section[data-testid="stSidebar"] div[data-baseweb="select"],
        section[data-testid="stSidebar"] div[data-baseweb="input"] {
            min-height: 46px !important;
            border-radius: 13px !important;
            background: #ffffff !important;
            border: 1px solid #dbe5f0 !important;
        }
        
        section[data-testid="stSidebar"] .stButton > button {
            min-height: 46px !important;
            border-radius: 13px !important;
            background: #ffffff !important;
            border: 1px solid #d3dce8 !important;
            box-shadow: 0 8px 18px rgba(15, 23, 42, 0.035) !important;
        }
        
        /* Hero target look */
        .hero-card {
            min-height: 190px !important;
            border-radius: 22px !important;
            padding: 34px 42px !important;
            margin-bottom: 1.35rem !important;
            background:
                radial-gradient(circle at 90% 48%, rgba(255, 79, 22, 0.78), transparent 30%),
                radial-gradient(circle at 72% 115%, rgba(249, 115, 22, 0.32), transparent 42%),
                linear-gradient(135deg, #071125 0%, #111a35 48%, #301d2a 75%, #9a3516 130%) !important;
            box-shadow: 0 24px 60px rgba(15, 23, 42, 0.16) !important;
        }
        
        .hero-card::before {
            right: -120px !important;
            top: -60px !important;
            width: 660px !important;
            height: 390px !important;
            opacity: 0.42 !important;
            background:
                repeating-radial-gradient(ellipse at center, rgba(255, 139, 61, 0.42) 0 1px, transparent 1px 13px) !important;
            transform: rotate(-12deg) !important;
        }
        
        .hero-title {
            font-size: 2.35rem !important;
            font-weight: 950 !important;
            letter-spacing: -0.06em !important;
            margin-bottom: 0.65rem !important;
        }
        
        .hero-subtitle {
            font-size: 1rem !important;
            max-width: 910px !important;
            line-height: 1.55 !important;
        }
        
        .chip-row {
            margin-top: 24px !important;
            gap: 11px !important;
        }
        
        .chip {
            min-height: 38px !important;
            padding: 8px 15px !important;
            border-radius: 13px !important;
            font-size: 0.8rem !important;
            font-weight: 900 !important;
            background: rgba(255, 255, 255, 0.13) !important;
            border: 1px solid rgba(255, 255, 255, 0.24) !important;
        }
        
        /* What this system does box */
        .top-note {
            grid-template-columns: 58px 1fr !important;
            padding: 22px 24px !important;
            border-radius: 18px !important;
            margin-bottom: 1.45rem !important;
            background:
                radial-gradient(circle at left, rgba(249, 115, 22, 0.11), transparent 34%),
                linear-gradient(135deg, #fffaf5 0%, #ffffff 100%) !important;
            border: 1px solid #fed7aa !important;
            border-left: 4px solid #fb923c !important;
        }
        
        .top-note-icon {
            width: 50px !important;
            height: 50px !important;
        }
        
        .top-note-title {
            font-size: 0.98rem !important;
        }
        
        .top-note-text {
            font-size: 0.94rem !important;
            line-height: 1.65 !important;
        }
        
        /* Tabs should look close to target */
        div[data-testid="stTabs"] {
            margin-top: 0.4rem !important;
        }
        
        div[data-testid="stTabs"] [role="tablist"] {
            border-bottom: 1px solid #cfd8e3 !important;
            gap: 0.25rem !important;
        }
        
        button[data-baseweb="tab"] {
            padding: 13px 12px !important;
            font-size: 0.84rem !important;
            font-weight: 850 !important;
            color: #475569 !important;
        }
        
        button[data-baseweb="tab"][aria-selected="true"],
        button[data-baseweb="tab"][aria-selected="true"] p {
            color: #ff4f16 !important;
            font-weight: 950 !important;
        }
        
        div[data-baseweb="tab-highlight"] {
            background-color: #ff4f16 !important;
            height: 3px !important;
        }
        
        /* Section spacing */
        .section-title {
            margin-top: 1.4rem !important;
            font-size: 1.45rem !important;
        }
        
        .section-subtitle {
            font-size: 0.92rem !important;
            margin-bottom: 1.15rem !important;
        }
        
        /* KPI cards closer to target */
        .kpi-card {
            min-height: 124px !important;
            border-radius: 18px !important;
            padding: 18px !important;
            border: 1px solid #dde6f0 !important;
            box-shadow: 0 10px 26px rgba(15, 23, 42, 0.055) !important;
        }
        
        .kpi-value {
            font-size: 1.55rem !important;
        }
        
        .kpi-icon {
            width: 40px !important;
            height: 40px !important;
            border-radius: 14px !important;
        }
        
        /* Feature/info cards */
        .feature-card,
        .info-card,
        .panel-card,
        .integration-status-card,
        .overview-card,
        .role-access-card,
        .approval-card {
            border-color: #dbe3ef !important;
            box-shadow: 0 12px 30px rgba(15, 23, 42, 0.055) !important;
        }
        
        /* Better form controls */
        .stTextInput input,
        .stTextArea textarea,
        div[data-baseweb="select"] {
            border-radius: 13px !important;
        }
        
        .stFormSubmitButton > button {
            min-height: 44px !important;
            border-radius: 13px !important;
            background: linear-gradient(135deg, #ff4f16 0%, #f97316 100%) !important;
            border: 1px solid #ff4f16 !important;
        }
        
        /* Login page final target */
        .login-screen {
            max-width: 1500px !important;
            margin: 1.5rem auto 0 auto !important;
        }
        
        .login-marketing-panel {
            min-height: 760px !important;
            border-radius: 34px !important;
            padding: 54px !important;
            background:
                radial-gradient(circle at 88% 95%, rgba(255, 79, 22, 0.45), transparent 35%),
                radial-gradient(circle at 25% 20%, rgba(37, 99, 235, 0.34), transparent 25%),
                linear-gradient(135deg, #031025 0%, #111752 48%, #2c1f65 72%, #7a2c19 125%) !important;
        }
        
        .login-brand-row {
            margin-bottom: 80px !important;
        }
        
        .login-brand-mark {
            width: 46px !important;
            height: 46px !important;
            border-radius: 17px !important;
        }
        
        .login-brand-name {
            font-size: 1.55rem !important;
        }
        
        .login-main-title {
            font-size: 3.75rem !important;
            line-height: 1.08 !important;
            max-width: 700px !important;
        }
        
        .login-main-copy {
            font-size: 1.08rem !important;
            max-width: 650px !important;
        }
        
        .login-feature-grid {
            gap: 16px !important;
        }
        
        .login-feature-card {
            min-height: 118px !important;
            border-radius: 19px !important;
        }
        
        .workspace-panel {
            min-height: 760px !important;
            border-radius: 34px !important;
            padding: 48px !important;
            box-shadow: 0 28px 76px rgba(15, 23, 42, 0.13) !important;
        }
        
        .workspace-title {
            font-size: 2rem !important;
        }
        
        .workspace-subtitle {
            font-size: 0.98rem !important;
            margin-bottom: 30px !important;
        }
        
        .workspace-option-card {
            min-height: 230px !important;
            border-radius: 22px !important;
            padding: 28px 20px !important;
        }
        
        .workspace-icon {
            width: 76px !important;
            height: 76px !important;
            font-size: 2rem !important;
        }
        
        .login-divider-label {
            margin-top: 26px !important;
        }
        
        /* Fix issue where HTML-like content appears too cramped */
        pre,
        code {
            white-space: pre-wrap !important;
        }
        
        /* Mobile */
        @media (max-width: 980px) {
            .main .block-container {
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }
        
            .login-marketing-panel,
            .workspace-panel {
                min-height: auto !important;
                padding: 30px !important;
            }
        
            .login-main-title {
                font-size: 2.6rem !important;
            }
        }
        /* Submit page layout spacing */
        .submit-page-shell {
            margin-top: 0.4rem;
        }
        
        .submit-main-card {
            background: #ffffff;
            border: 1px solid #dbe3ef;
            border-radius: 20px;
            padding: 22px;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.055);
        }
        
        .submit-form-intro {
            margin-bottom: 18px !important;
        }
        
        .submit-form-title {
            font-size: 1.08rem !important;
            font-weight: 950 !important;
            color: #07112f !important;
            letter-spacing: -0.03em !important;
            margin-bottom: 6px !important;
        }
        
        .submit-form-subtitle {
            color: #64748b !important;
            font-size: 0.88rem !important;
            line-height: 1.6 !important;
            max-width: 720px !important;
        }
        
        /* Make Streamlit container borders look like SaaS cards */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 20px !important;
            border-color: #dbe3ef !important;
            box-shadow: 0 12px 30px rgba(15, 23, 42, 0.05) !important;
        }
        
        /* Submit form fields */
        .stTextInput label,
        .stTextArea label,
        .stSelectbox label,
        .stCheckbox label {
            color: #334155 !important;
            font-weight: 850 !important;
            font-size: 0.82rem !important;
        }
        
        .stTextInput input {
            min-height: 44px !important;
            border-radius: 13px !important;
            border: 1px solid #dbe3ef !important;
            background: #ffffff !important;
            color: #07112f !important;
        }
        
        .stTextArea textarea {
            border-radius: 15px !important;
            border: 1px solid #dbe3ef !important;
            background: #ffffff !important;
            color: #07112f !important;
            min-height: 160px !important;
        }
        
        .stCheckbox {
            margin-top: 0.3rem !important;
            margin-bottom: 0.65rem !important;
        }
        
        .stCheckbox label p {
            font-size: 0.86rem !important;
            color: #334155 !important;
            font-weight: 800 !important;
        }
        
        /* Submit button target look */
        .stFormSubmitButton > button {
            width: 100% !important;
            min-height: 46px !important;
            border-radius: 13px !important;
            background: linear-gradient(135deg, #ff4f16 0%, #f97316 100%) !important;
            border: 1px solid #ff4f16 !important;
            color: #ffffff !important;
            font-weight: 950 !important;
            box-shadow: 0 12px 26px rgba(249, 115, 22, 0.24) !important;
        }
        
        .stFormSubmitButton > button:hover {
            background: linear-gradient(135deg, #ea580c 0%, #fb923c 100%) !important;
            color: #ffffff !important;
            border-color: #ea580c !important;
            box-shadow: 0 15px 32px rgba(249, 115, 22, 0.3) !important;
        }
        
        /* Right-side feature cards */
        .feature-card {
            border-radius: 20px !important;
            padding: 22px !important;
            min-height: 142px !important;
            background: #ffffff !important;
            border: 1px solid #dbe3ef !important;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.055) !important;
            grid-template-columns: 56px 1fr !important;
            gap: 18px !important;
        }
        
        .feature-icon {
            width: 50px !important;
            height: 50px !important;
            border-radius: 17px !important;
            font-size: 1.22rem !important;
        }
        
        .feature-title {
            font-size: 1rem !important;
            font-weight: 950 !important;
            color: #07112f !important;
            margin-bottom: 8px !important;
        }
        
        .feature-text {
            color: #475569 !important;
            font-size: 0.9rem !important;
            line-height: 1.65 !important;
        }
        
        /* Simulation block */
        .simulation-success-card {
            background: linear-gradient(135deg, #fff7ed 0%, #ffffff 100%) !important;
            border: 1px solid #fed7aa !important;
            border-radius: 16px !important;
            padding: 16px 18px !important;
            color: #9a3412 !important;
            font-size: 0.9rem !important;
            line-height: 1.6 !important;
            margin-top: 14px !important;
        }
        
        /* Latest AI Result spacing */
        .latest-result-shell {
            margin-top: 1.3rem;
        }
        
        .result-callout {
            border-radius: 17px !important;
            padding: 16px 18px !important;
            margin: 18px 0 18px 0 !important;
            background: #fffbeb !important;
            border: 1px solid #fde68a !important;
        }
        
        .result-callout-icon {
            width: 36px !important;
            height: 36px !important;
            border-radius: 13px !important;
        }
        
        .result-callout-title {
            font-size: 0.95rem !important;
        }
        
        .result-callout-text {
            font-size: 0.9rem !important;
        }
        
        /* Latest result summary boxes */
        .result-summary-box {
            border-radius: 15px !important;
            padding: 15px 17px !important;
            margin-bottom: 12px !important;
            font-size: 0.92rem !important;
            line-height: 1.6 !important;
        }
        
        /* Make JSON/expander cleaner */
        details {
            border-radius: 15px !important;
            border: 1px solid #dbe3ef !important;
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.035) !important;
        }
        
        details summary {
            font-size: 0.88rem !important;
            color: #334155 !important;
            font-weight: 900 !important;
        }
        
        /* Better tabs inside result area */
        .latest-result-shell button[data-baseweb="tab"] {
            font-size: 0.83rem !important;
            padding: 12px 10px !important;
        }
        
        /* Mobile submit page */
        @media (max-width: 900px) {
            .feature-card {
                min-height: auto !important;
            }

            .submit-main-card {
                padding: 18px !important;
            }
        }

        .ops-page-shell {
            margin-top: 0.4rem;
        }

        /* Better KPI card sizing on operations page */
        .ops-page-shell .kpi-card {
            min-height: 128px !important;
            border-radius: 19px !important;
            padding: 18px 18px 16px 18px !important;
            box-shadow: 0 12px 30px rgba(15, 23, 42, 0.05) !important;
        }

        .ops-page-shell .kpi-value {
            font-size: 1.52rem !important;
        }

        .ops-page-shell .kpi-sub {
            font-size: 0.77rem !important;
        }

        /* Operations chart containers */
        .ops-chart-card {
            background: #ffffff;
            border: 1px solid #dbe3ef;
            border-radius: 20px;
            padding: 18px;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.055);
            margin-bottom: 16px;
            min-height: 350px;
        }

        .ops-chart-wide-card {
            background: #ffffff;
            border: 1px solid #dbe3ef;
            border-radius: 20px;
            padding: 18px;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.055);
            margin-bottom: 18px;
        }

        .ops-table-card {
            background: #ffffff;
            border: 1px solid #dbe3ef;
            border-radius: 20px;
            padding: 18px;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.055);
            margin-bottom: 18px;
        }

        .ops-detail-card {
            background: #ffffff;
            border: 1px solid #dbe3ef;
            border-radius: 20px;
            padding: 18px;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.055);
            margin-top: 12px;
            margin-bottom: 18px;
        }

        .chart-panel-title {
            font-size: 0.98rem !important;
            font-weight: 950 !important;
            color: #07112f !important;
            letter-spacing: -0.025em !important;
            margin-bottom: 5px !important;
        }

        .chart-panel-subtitle {
            color: #64748b !important;
            font-size: 0.84rem !important;
            line-height: 1.5 !important;
            margin-bottom: 14px !important;
        }

        /* Streamlit Altair chart polish */
        .ops-page-shell div[data-testid="stVegaLiteChart"],
        .ops-page-shell div[data-testid="stArrowVegaLiteChart"] {
            border-radius: 16px !important;
            border: 1px solid #e2e8f0 !important;
            background: #ffffff !important;
            box-shadow: none !important;
            padding: 8px !important;
        }

        /* Table section */
        .table-action-row {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 15px;
            padding: 12px 14px;
            margin: 4px 0 14px 0 !important;
        }

        .table-meta-text {
            color: #64748b !important;
            font-size: 0.84rem !important;
            line-height: 1.45 !important;
        }

        .ops-page-shell .stDownloadButton > button {
            min-height: 39px !important;
            border-radius: 12px !important;
            background: #ffffff !important;
            color: #07112f !important;
            border: 1px solid #cbd5e1 !important;
            font-weight: 850 !important;
        }

        .ops-page-shell .stDownloadButton > button:hover {
            color: #ff4f16 !important;
            border-color: #ff4f16 !important;
        }

        /* Dataframe polish */
        .ops-page-shell div[data-testid="stDataFrame"] {
            border-radius: 16px !important;
            border: 1px solid #dbe3ef !important;
            overflow: hidden !important;
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.035) !important;
        }

        /* Request selector */
        .request-selector-label {
            color: #334155 !important;
            font-size: 0.84rem !important;
            font-weight: 900 !important;
            margin-top: 16px !important;
            margin-bottom: 7px !important;
        }

        .ops-page-shell div[data-baseweb="select"] {
            border-radius: 13px !important;
        }

        /* Detail review messages */
        .detail-message {
            border-radius: 15px !important;
            padding: 15px 17px !important;
            margin-bottom: 11px !important;
            font-size: 0.91rem !important;
            line-height: 1.6 !important;
        }

        .detail-message-blue {
            background: #eff6ff !important;
            border-color: #bfdbfe !important;
            color: #1d4ed8 !important;
        }

        .detail-message-green {
            background: #ecfdf5 !important;
            border-color: #bbf7d0 !important;
            color: #047857 !important;
        }

        .detail-message-yellow {
            background: #fffbeb !important;
            border-color: #fde68a !important;
            color: #92400e !important;
        }

        /* Make detailed review tabs cleaner */
        .ops-detail-card button[data-baseweb="tab"] {
            font-size: 0.82rem !important;
            padding: 11px 10px !important;
        }

        /* Empty state */
        .ops-empty-state-card {
            background: #ffffff;
            border: 1px solid #dbe3ef;
            border-radius: 20px;
            padding: 22px;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.055);
        }

        /* Better info alert */
        .ops-page-shell div[data-testid="stAlert"] {
            border-radius: 15px !important;
        }

        /* Mobile */
        @media (max-width: 900px) {
            .ops-chart-card,
            .ops-chart-wide-card,
            .ops-table-card,
            .ops-detail-card {
                padding: 15px !important;
            }
        }
        

        .approval-page-shell {
            margin-top: 0.35rem;
        }

        /* Streamlit bordered containers used for approval cards */
        .approval-page-shell div[data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid #dbe3ef !important;
            border-radius: 22px !important;
            background: #ffffff !important;
            box-shadow: 0 16px 38px rgba(15, 23, 42, 0.06) !important;
            padding: 0 !important;
            overflow: hidden !important;
            margin-bottom: 20px !important;
        }

        .approval-page-shell div[data-testid="stVerticalBlockBorderWrapper"] > div {
            padding: 0 !important;
        }

        /* Card content */
        .approval-ticket-card {
            padding: 22px 24px 8px 24px;
        }

        .approval-ticket-grid {
            display: grid;
            grid-template-columns: minmax(0, 1.45fr) 0.62fr 0.72fr 0.78fr;
            gap: 0;
            align-items: flex-start;
            margin-bottom: 18px;
        }

        .approval-main-info {
            padding-right: 22px;
        }

        .approval-ticket-title-row {
            display: flex;
            align-items: flex-start;
            gap: 12px;
            margin-bottom: 8px;
        }

        .approval-critical-icon {
            width: 34px;
            height: 34px;
            border-radius: 999px;
            background: #fef2f2;
            color: #dc2626;
            border: 1px solid #fecaca;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 950;
            flex: 0 0 auto;
        }

        .approval-title {
            color: #07112f;
            font-size: 1.08rem;
            font-weight: 950;
            line-height: 1.28;
            letter-spacing: -0.035em;
            margin-top: 2px;
        }

        .approval-summary {
            color: #64748b;
            font-size: 0.9rem;
            line-height: 1.58;
            margin-left: 46px;
            max-width: 720px;
        }

        .approval-stat-cell {
            min-height: 76px;
            border-left: 1px solid #e2e8f0;
            padding-left: 22px;
            padding-right: 14px;
        }

        .approval-stat-label {
            color: #64748b;
            font-size: 0.72rem;
            font-weight: 900;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            margin-bottom: 8px;
        }

        .approval-stat-value {
            color: #07112f;
            font-size: 1rem;
            font-weight: 950;
            line-height: 1.25;
        }

        .approval-stat-value.high {
            color: #dc2626;
        }

        .approval-badge-row {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 8px;
            margin: 8px 0 16px 46px;
        }

        .approval-soft-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            border-radius: 999px;
            padding: 7px 11px;
            font-size: 0.76rem;
            font-weight: 900;
            border: 1px solid transparent;
            white-space: nowrap;
        }

        .approval-soft-badge.danger {
            background: #fef2f2;
            color: #b91c1c;
            border-color: #fecaca;
        }

        .approval-soft-badge.warning {
            background: #fff7ed;
            color: #c2410c;
            border-color: #fed7aa;
        }

        .approval-soft-badge.purple {
            background: #f5f3ff;
            color: #6d28d9;
            border-color: #ddd6fe;
        }

        .approval-soft-badge.success {
            background: #ecfdf5;
            color: #047857;
            border-color: #bbf7d0;
        }

        .approval-reason-strip {
            display: grid;
            grid-template-columns: 38px 1fr;
            gap: 13px;
            align-items: flex-start;
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            border-left: 4px solid #2563eb;
            border-radius: 16px;
            padding: 14px 16px;
            margin: 14px 0 16px 0;
        }

        .approval-reason-strip-icon {
            width: 32px;
            height: 32px;
            border-radius: 11px;
            background: #dbeafe;
            color: #1d4ed8;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 950;
        }

        .approval-reason-strip-title {
            color: #1d4ed8;
            font-size: 0.76rem;
            font-weight: 950;
            letter-spacing: 0.07em;
            text-transform: uppercase;
            margin-bottom: 4px;
        }

        .approval-reason-strip-text {
            color: #1e3a8a;
            font-size: 0.9rem;
            line-height: 1.55;
            font-weight: 700;
        }

        .approval-meta-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 14px;
            flex-wrap: wrap;
            border-top: 1px solid #e2e8f0;
            padding-top: 14px;
            color: #64748b;
            font-size: 0.8rem;
            font-weight: 800;
        }

        .approval-request-pill {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            color: #475569;
            border-radius: 999px;
            padding: 7px 11px;
            max-width: 100%;
            word-break: break-word;
        }

        /* Buttons inside approval queue */
        .approval-page-shell .stButton > button {
            min-height: 46px !important;
            border-radius: 13px !important;
            font-weight: 950 !important;
            box-shadow: none !important;
            margin-bottom: 18px !important;
        }

        .approval-page-shell button[data-testid="stBaseButton-primary"],
        .approval-page-shell .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%) !important;
            color: #ffffff !important;
            border: 1px solid #1d4ed8 !important;
            box-shadow: 0 12px 28px rgba(37, 99, 235, 0.20) !important;
        }

        .approval-page-shell button[data-testid="stBaseButton-primary"]:hover,
        .approval-page-shell .stButton > button[kind="primary"]:hover {
            color: #ffffff !important;
            border-color: #1e40af !important;
            transform: translateY(-1px);
        }

        .approval-page-shell button[data-testid="stBaseButton-secondary"],
        .approval-page-shell .stButton > button[kind="secondary"] {
            background: #ffffff !important;
            color: #dc2626 !important;
            border: 1px solid #f87171 !important;
        }

        .approval-page-shell button[data-testid="stBaseButton-secondary"]:hover,
        .approval-page-shell .stButton > button[kind="secondary"]:hover {
            color: #b91c1c !important;
            border-color: #dc2626 !important;
            background: #fff7f7 !important;
            transform: translateY(-1px);
        }

        .approval-result-card {
            background: #ffffff;
            border: 1px solid #dbe3ef;
            border-radius: 18px;
            padding: 18px;
            box-shadow: 0 12px 30px rgba(15, 23, 42, 0.05);
            margin-bottom: 16px;
        }

        .approval-result-title {
            color: #07112f;
            font-size: 0.98rem;
            font-weight: 950;
            margin-bottom: 6px;
        }

        .approval-result-text {
            color: #64748b;
            font-size: 0.88rem;
            line-height: 1.55;
        }

        /* Empty state */
        .approval-empty-card {
            background: #ffffff;
            border: 1px solid #dbe3ef;
            border-radius: 20px;
            padding: 22px;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.055);
        }

        /* Responsive */
        @media (max-width: 1050px) {
            .approval-ticket-grid {
                grid-template-columns: 1fr;
                gap: 14px;
            }

            .approval-stat-cell {
                border-left: 0;
                border-top: 1px solid #e2e8f0;
                padding-left: 0;
                padding-top: 14px;
            }

            .approval-summary,
            .approval-badge-row {
                margin-left: 0;
            }
        }
        .integration-page-shell {
            margin-top: 0.35rem;
        }

        .integration-status-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 20px;
        }

        .integration-v2-card {
            background: #ffffff;
            border: 1px solid #dbe3ef;
            border-radius: 18px;
            padding: 18px;
            min-height: 132px;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.055);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .integration-v2-top {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 12px;
        }

        .integration-v2-label {
            color: #64748b;
            font-size: 0.7rem;
            font-weight: 950;
            letter-spacing: 0.075em;
            text-transform: uppercase;
        }

        .integration-v2-icon {
            width: 36px;
            height: 36px;
            border-radius: 13px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 950;
            border: 1px solid transparent;
        }

        .integration-v2-value {
            color: #07112f;
            font-size: 1.25rem;
            font-weight: 950;
            letter-spacing: -0.04em;
            margin-bottom: 6px;
        }

        .integration-v2-subtitle {
            color: #64748b;
            font-size: 0.8rem;
            line-height: 1.45;
        }

        .contract-intro-card {
            background:
                radial-gradient(circle at top right, rgba(37, 99, 235, 0.065), transparent 34%),
                linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid #dbe3ef;
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.055);
            margin-bottom: 16px;
        }

        .contract-intro-title {
            color: #07112f;
            font-size: 1rem;
            font-weight: 950;
            letter-spacing: -0.025em;
            margin-bottom: 7px;
        }

        .contract-intro-text {
            color: #64748b;
            font-size: 0.88rem;
            line-height: 1.58;
        }

        .contract-metric-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 14px;
            margin-bottom: 16px;
        }

        .contract-metric-card {
            background: #ffffff;
            border: 1px solid #dbe3ef;
            border-radius: 18px;
            padding: 18px;
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.05);
            min-height: 124px;
            position: relative;
        }

        .contract-metric-icon {
            position: absolute;
            top: 16px;
            right: 16px;
            width: 34px;
            height: 34px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 950;
            border: 1px solid transparent;
        }

        .contract-metric-label {
            color: #64748b;
            font-size: 0.68rem;
            font-weight: 950;
            letter-spacing: 0.075em;
            text-transform: uppercase;
            margin-bottom: 11px;
            max-width: calc(100% - 46px);
        }

        .contract-metric-value {
            color: #07112f;
            font-size: 1.18rem;
            font-weight: 950;
            letter-spacing: -0.04em;
            line-height: 1.2;
            margin-bottom: 8px;
            word-break: break-word;
        }

        .contract-metric-subtitle {
            color: #64748b;
            font-size: 0.78rem;
            line-height: 1.45;
        }

        .benchmark-runner-card {
            background: #ffffff;
            border: 1px solid #dbe3ef;
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.055);
            margin-bottom: 16px;
        }

        .benchmark-runner-title {
            color: #07112f;
            font-size: 1rem;
            font-weight: 950;
            letter-spacing: -0.025em;
            margin-bottom: 6px;
        }

        .benchmark-runner-text {
            color: #64748b;
            font-size: 0.86rem;
            line-height: 1.52;
        }

        .benchmark-page-shell .stButton > button,
        .integration-page-shell .stButton > button {
            border-radius: 12px !important;
            font-weight: 900 !important;
        }

        .integration-page-shell .stButton > button:hover {
            transform: translateY(-1px);
        }

        .benchmark-success-strip {
            background: #ecfdf5;
            border: 1px solid #bbf7d0;
            color: #047857;
            border-radius: 14px;
            padding: 13px 15px;
            font-size: 0.86rem;
            font-weight: 800;
            margin: 14px 0 18px 0;
        }

        .benchmark-chart-shell div[data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid #dbe3ef !important;
            border-radius: 18px !important;
            background: #ffffff !important;
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.05) !important;
        }

        .integration-page-shell div[data-testid="stDataFrame"] {
            border-radius: 14px !important;
            border: 1px solid #dbe3ef !important;
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.045) !important;
        }

        .integration-page-shell details {
            margin-bottom: 12px;
        }

        .integration-page-shell div[data-testid="stAlert"] {
            border-radius: 14px !important;
        }

        @media (max-width: 1050px) {
            .integration-status-grid,
            .contract-metric-grid {
                grid-template-columns: 1fr 1fr;
            }
        }

        @media (max-width: 720px) {
            .integration-status-grid,
            .contract-metric-grid {
                grid-template-columns: 1fr;
            }
        }

        .observability-page-shell {
            margin-top: 0.35rem;
        }

        .obs-intro-grid {
            display: grid;
            grid-template-columns: 0.95fr 2.05fr;
            gap: 16px;
            margin-bottom: 18px;
        }

        .obs-window-card {
            background: #ffffff;
            border: 1px solid #dbe3ef;
            border-radius: 20px;
            padding: 18px;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.055);
            min-height: 132px;
        }

        .obs-window-title {
            color: #07112f;
            font-size: 0.96rem;
            font-weight: 950;
            letter-spacing: -0.025em;
            margin-bottom: 6px;
        }

        .obs-window-text {
            color: #64748b;
            font-size: 0.84rem;
            line-height: 1.52;
            margin-bottom: 12px;
        }

        .obs-intro-card-v2 {
            background:
                radial-gradient(circle at top right, rgba(255, 79, 22, 0.10), transparent 34%),
                linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid #dbe3ef;
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.055);
            min-height: 132px;
        }

        .obs-intro-eyebrow {
            color: #ff4f16;
            font-size: 0.72rem;
            font-weight: 950;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 8px;
        }

        .obs-intro-title-v2 {
            color: #07112f;
            font-size: 1.1rem;
            font-weight: 950;
            letter-spacing: -0.035em;
            margin-bottom: 7px;
        }

        .obs-intro-text-v2 {
            color: #475569;
            font-size: 0.88rem;
            line-height: 1.58;
            max-width: 900px;
        }

        .obs-section-wrapper {
            background: #ffffff;
            border: 1px solid #dbe3ef;
            border-radius: 22px;
            padding: 20px;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.055);
            margin-bottom: 18px;
        }

        .obs-section-heading-row {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 16px;
            flex-wrap: wrap;
            margin-bottom: 16px;
        }

        .obs-section-heading-left {
            max-width: 820px;
        }

        .obs-section-mini-label {
            color: #ff4f16;
            font-size: 0.68rem;
            font-weight: 950;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 5px;
        }

        .obs-section-heading-title {
            color: #07112f;
            font-size: 1rem;
            font-weight: 950;
            letter-spacing: -0.03em;
            margin-bottom: 5px;
        }

        .obs-section-heading-text {
            color: #64748b;
            font-size: 0.86rem;
            line-height: 1.55;
        }

        .obs-section-badge {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            padding: 7px 11px;
            border-radius: 999px;
            background: #fff7ed;
            color: #c2410c;
            border: 1px solid #fed7aa;
            font-size: 0.76rem;
            font-weight: 900;
            white-space: nowrap;
        }

        .obs-alert-success-box {
            background: #ecfdf5;
            border: 1px solid #bbf7d0;
            color: #047857;
            border-radius: 15px;
            padding: 14px 16px;
            font-size: 0.88rem;
            font-weight: 800;
            margin: 8px 0 14px 0;
        }

        .obs-feedback-card {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 18px;
            padding: 18px;
            margin-bottom: 16px;
        }

        .obs-feedback-title {
            color: #07112f;
            font-size: 0.98rem;
            font-weight: 950;
            letter-spacing: -0.025em;
            margin-bottom: 6px;
        }

        .obs-feedback-text {
            color: #64748b;
            font-size: 0.86rem;
            line-height: 1.55;
        }

        .obs-table-note {
            color: #64748b;
            font-size: 0.84rem;
            line-height: 1.5;
            margin: 4px 0 12px 0;
        }

        .obs-json-note {
            background: #f8fafc;
            border: 1px dashed #cbd5e1;
            color: #64748b;
            border-radius: 14px;
            padding: 13px 15px;
            font-size: 0.84rem;
            line-height: 1.5;
            margin-bottom: 12px;
        }

        .observability-page-shell div[data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid #dbe3ef !important;
            border-radius: 22px !important;
            background: #ffffff !important;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.055) !important;
        }

        .observability-page-shell div[data-testid="stDataFrame"] {
            border-radius: 14px !important;
            border: 1px solid #dbe3ef !important;
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.045) !important;
        }

        .observability-page-shell details {
            margin-bottom: 12px;
        }

        .observability-page-shell div[data-testid="stAlert"] {
            border-radius: 14px !important;
        }

        @media (max-width: 900px) {
            .obs-intro-grid {
                grid-template-columns: 1fr;
            }
        }

        .project-page-shell {
            margin-top: 0.35rem;
        }

        .project-intro-panel-v2 {
            position: relative;
            overflow: hidden;
            background:
                radial-gradient(circle at 88% 18%, rgba(255, 79, 22, 0.18), transparent 34%),
                radial-gradient(circle at 8% 85%, rgba(37, 99, 235, 0.10), transparent 32%),
                linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid #dbe3ef;
            border-radius: 24px;
            padding: 24px;
            box-shadow: 0 16px 40px rgba(15, 23, 42, 0.065);
            margin-bottom: 18px;
        }

        .project-intro-panel-v2::after {
            content: "";
            position: absolute;
            right: -120px;
            bottom: -120px;
            width: 420px;
            height: 250px;
            opacity: 0.24;
            background:
                repeating-radial-gradient(ellipse at center, rgba(255, 79, 22, 0.42) 0 1px, transparent 1px 14px);
            transform: rotate(-10deg);
        }

        .project-intro-content {
            position: relative;
            z-index: 1;
        }

        .project-eyebrow {
            color: #ff4f16;
            font-size: 0.72rem;
            font-weight: 950;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 8px;
        }

        .project-main-title {
            color: #07112f;
            font-size: 1.55rem;
            font-weight: 950;
            letter-spacing: -0.055em;
            line-height: 1.12;
            margin-bottom: 10px;
        }

        .project-main-text {
            color: #475569;
            font-size: 0.92rem;
            line-height: 1.65;
            max-width: 980px;
        }

        .project-chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 9px;
            margin-top: 16px;
        }

        .project-chip {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            padding: 7px 11px;
            border-radius: 999px;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            color: #334155;
            font-size: 0.76rem;
            font-weight: 850;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        }

        .project-overview-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 14px;
            margin-bottom: 18px;
        }

        .project-capability-card {
            background: #ffffff;
            border: 1px solid #dbe3ef;
            border-radius: 20px;
            padding: 22px;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.055);
            height: 250px !important;
            min-height: 250px !important;
            display: flex !important;
            flex-direction: column !important;
        }

        .project-capability-text {
            flex: 1 !important;
        }

        .project-capability-icon {
            width: 44px;
            height: 44px;
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 950;
            margin-bottom: 14px;
            border: 1px solid transparent;
        }

        .project-capability-title {
            color: #07112f;
            font-size: 0.98rem;
            font-weight: 950;
            letter-spacing: -0.025em;
            margin-bottom: 8px;
        }

        .project-capability-text {
            color: #475569;
            font-size: 0.87rem;
            line-height: 1.62;
        }

        .project-workflow-panel {
            background: #ffffff;
            border: 1px solid #dbe3ef;
            border-radius: 22px;
            padding: 20px;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.055);
            margin-bottom: 18px;
        }

        .project-workflow-grid {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 12px;
        }

        .project-workflow-step {
            position: relative;
            background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid #e2e8f0;
            border-radius: 18px;
            padding: 16px;
            min-height: 158px;
        }

        .project-step-number {
            width: 31px;
            height: 31px;
            border-radius: 999px;
            background: #fff7ed;
            color: #c2410c;
            border: 1px solid #fed7aa;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 950;
            font-size: 0.78rem;
            margin-bottom: 12px;
        }

        .project-step-title {
            color: #07112f;
            font-size: 0.86rem;
            font-weight: 950;
            margin-bottom: 6px;
        }

        .project-step-text {
            color: #64748b;
            font-size: 0.79rem;
            line-height: 1.48;
        }

        .project-architecture-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 14px;
            margin-bottom: 18px;
        }

        .project-architecture-card {
            background: #ffffff;
            border: 1px solid #dbe3ef;
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.055);
            min-height: 160px;
            margin-bottom: 14px;
        }

        .project-architecture-title {
            color: #07112f;
            font-size: 0.98rem;
            font-weight: 950;
            letter-spacing: -0.025em;
            margin-bottom: 8px;
        }

        .project-architecture-text {
            color: #475569;
            font-size: 0.88rem;
            line-height: 1.62;
        }

        .role-card-v2 {
            background: #ffffff;
            border: 1px solid #dbe3ef;
            border-radius: 22px;
            padding: 20px;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.055);
            margin-bottom: 16px;
            min-height: 255px;
        }

        .role-card-top-v2 {
            display: flex;
            align-items: center;
            gap: 13px;
            margin-bottom: 12px;
        }

        .role-card-icon-v2 {
            width: 44px;
            height: 44px;
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 950;
            border: 1px solid transparent;
        }

        .role-card-title-v2 {
            color: #07112f;
            font-size: 1rem;
            font-weight: 950;
            letter-spacing: -0.025em;
        }

        .role-card-text-v2 {
            color: #64748b;
            font-size: 0.87rem;
            line-height: 1.58;
            margin-bottom: 14px;
        }

        .role-pill-row-v2 {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .role-pill-v2 {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            padding: 7px 10px;
            border-radius: 999px;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            color: #334155;
            font-size: 0.76rem;
            font-weight: 850;
        }

        .portfolio-proof-card {
            background: #ffffff;
            border: 1px solid #dbe3ef;
            border-radius: 20px;
            padding: 19px;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.055);
            min-height: 160px;
        }

        @media (max-width: 1100px) {
            .project-overview-grid,
            .project-workflow-grid {
                grid-template-columns: repeat(2, 1fr);
            }

            .project-architecture-grid {
                grid-template-columns: 1fr;
            }
        }

        @media (max-width: 720px) {
            .project-overview-grid,
            .project-workflow-grid {
                grid-template-columns: 1fr;
            }
        }

        /* ============================
           LOGIN PAGE PATCH - FINAL
           ============================ */

        .login-screen-v2 {
            max-width: 1500px;
            margin: 1.5rem auto 0 auto;
        }

        .login-screen-v2 .login-grid-v2 {
            display: grid;
            grid-template-columns: 1.05fr 0.95fr;
            gap: 32px;
            align-items: stretch;
        }

        .login-marketing-panel-v2 {
            min-height: 760px;
            border-radius: 34px;
            padding: 54px;
            color: #ffffff;
            position: relative;
            overflow: hidden;
            background:
                radial-gradient(circle at 88% 95%, rgba(255, 79, 22, 0.45), transparent 35%),
                radial-gradient(circle at 25% 20%, rgba(37, 99, 235, 0.34), transparent 25%),
                linear-gradient(135deg, #031025 0%, #111752 48%, #2c1f65 72%, #7a2c19 125%);
            box-shadow: 0 26px 70px rgba(15, 23, 42, 0.22);
            border: 1px solid rgba(255,255,255,0.12);
        }

        .login-marketing-panel-v2::after {
            content: "";
            position: absolute;
            left: -90px;
            bottom: -120px;
            width: 720px;
            height: 320px;
            opacity: 0.32;
            background:
                repeating-radial-gradient(
                    ellipse at center,
                    rgba(96, 165, 250, 0.36) 0 1px,
                    transparent 1px 15px
                );
            transform: rotate(-8deg);
        }

        .login-brand-row-v2 {
            display: flex;
            align-items: center;
            gap: 14px;
            position: relative;
            z-index: 1;
            margin-bottom: 80px;
        }

        .login-brand-mark-v2 {
            width: 46px;
            height: 46px;
            border-radius: 17px;
            background:
                radial-gradient(circle at 30% 30%, #ffffff 0 9%, transparent 10%),
                conic-gradient(from 40deg, #2563eb, #8b5cf6, #fb7185, #fb923c, #2563eb);
            box-shadow: 0 16px 34px rgba(96, 165, 250, 0.28);
        }

        .login-brand-name-v2 {
            font-size: 1.55rem;
            font-weight: 950;
            letter-spacing: -0.05em;
        }

        .login-pill-v2 {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 16px;
            border-radius: 999px;
            background: rgba(255,255,255,0.10);
            border: 1px solid rgba(255,255,255,0.16);
            color: #93c5fd;
            font-size: 0.78rem;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            position: relative;
            z-index: 1;
            margin-bottom: 28px;
        }

        .login-main-title-v2 {
            position: relative;
            z-index: 1;
            font-size: 3.75rem;
            line-height: 1.08;
            font-weight: 950;
            letter-spacing: -0.065em;
            max-width: 700px;
            margin-bottom: 22px;
        }

        .login-gradient-word-v2 {
            background: linear-gradient(90deg, #8b5cf6 0%, #fb7185 45%, #fb923c 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .login-main-copy-v2 {
            position: relative;
            z-index: 1;
            max-width: 650px;
            color: rgba(255,255,255,0.78);
            font-size: 1.08rem;
            line-height: 1.65;
            margin-bottom: 34px;
        }

        .login-feature-grid-v2 {
            position: relative;
            z-index: 1;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-top: 24px;
        }

        .login-feature-card-v2 {
            min-height: 118px;
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.14);
            border-radius: 19px;
            padding: 18px;
            display: grid;
            grid-template-columns: 44px 1fr;
            gap: 14px;
            align-items: center;
            backdrop-filter: blur(8px);
        }

        .login-feature-icon-v2 {
            width: 44px;
            height: 44px;
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
            background: rgba(37, 99, 235, 0.32);
            border: 1px solid rgba(147, 197, 253, 0.25);
        }

        .login-feature-title-v2 {
            font-size: 0.96rem;
            font-weight: 950;
            margin-bottom: 4px;
        }

        .login-feature-text-v2 {
            color: rgba(255,255,255,0.68);
            font-size: 0.82rem;
            line-height: 1.45;
        }

        .login-security-note-v2 {
            position: absolute;
            left: 54px;
            bottom: 34px;
            z-index: 1;
            color: rgba(255,255,255,0.72);
            font-size: 0.85rem;
            display: flex;
            align-items: center;
            gap: 9px;
        }

        /* Right login card wrapper */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.login-panel-anchor-v2) {
            min-height: 760px !important;
            border-radius: 34px !important;
            padding: 0 !important;
            background:
                radial-gradient(circle at 50% 0%, rgba(37, 99, 235, 0.06), transparent 35%),
                #ffffff !important;
            border: 1px solid #dbe3ef !important;
            box-shadow: 0 28px 76px rgba(15, 23, 42, 0.13) !important;
            overflow: hidden !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.login-panel-anchor-v2) > div {
            padding: 48px !important;
        }

        .login-panel-anchor-v2 {
            display: none;
        }

        .workspace-title-v2 {
            font-size: 2rem;
            font-weight: 950;
            letter-spacing: -0.05em;
            color: #07112f;
            text-align: center;
            margin-bottom: 8px;
        }

        .workspace-subtitle-v2 {
            color: #64748b;
            text-align: center;
            font-size: 0.98rem;
            margin-bottom: 30px;
        }

        .workspace-card-row-v2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-bottom: 16px;
        }

        .workspace-option-card-v2 {
            min-height: 230px;
            border-radius: 22px;
            border: 1px solid #dbe3ef;
            background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
            padding: 28px 20px;
            text-align: center;
            position: relative;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
        }

        .workspace-option-card-v2.selected {
            border: 2px solid #8ea5ff;
            box-shadow: 0 16px 40px rgba(37, 99, 235, 0.14);
            background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%);
        }

        .workspace-check-v2 {
            position: absolute;
            top: 14px;
            right: 14px;
            width: 26px;
            height: 26px;
            border-radius: 999px;
            background: #2563eb;
            color: white;
            font-size: 0.82rem;
            font-weight: 950;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .workspace-icon-v2 {
            width: 76px;
            height: 76px;
            border-radius: 999px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 6px auto 16px auto;
            font-size: 2rem;
            border: 1px solid;
        }

        .workspace-icon-v2.admin {
            background: #eff6ff;
            color: #2563eb;
            border-color: #bfdbfe;
        }

        .workspace-icon-v2.analyst {
            background: #fff7ed;
            color: #f97316;
            border-color: #fed7aa;
        }

        .workspace-card-title-v2 {
            color: #07112f;
            font-weight: 950;
            font-size: 1rem;
            margin-bottom: 8px;
        }

        .workspace-card-text-v2 {
            color: #64748b;
            font-size: 0.86rem;
            line-height: 1.55;
        }

        .login-divider-label-v2 {
            display: flex;
            align-items: center;
            gap: 14px;
            color: #64748b;
            font-size: 0.86rem;
            margin: 24px 0 18px 0;
        }

        .login-divider-label-v2::before,
        .login-divider-label-v2::after {
            content: "";
            height: 1px;
            background: #e2e8f0;
            flex: 1;
        }

        .login-footer-text-v2 {
            text-align: center;
            color: #64748b;
            font-size: 0.78rem;
            margin-top: 18px;
            line-height: 1.5;
        }

        /* Login page buttons */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.login-panel-anchor-v2) .stButton > button {
            min-height: 42px !important;
            border-radius: 13px !important;
            background: #ffffff !important;
            color: #07112f !important;
            border: 1px solid #cbd5e1 !important;
            font-weight: 900 !important;
            box-shadow: none !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.login-panel-anchor-v2) .stButton > button:hover {
            color: #2563eb !important;
            border-color: #8ea5ff !important;
            box-shadow: 0 8px 20px rgba(37, 99, 235, 0.12) !important;
        }

        /* Login submit button */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.login-panel-anchor-v2) .stFormSubmitButton > button {
            width: 100% !important;
            min-height: 50px !important;
            border-radius: 13px !important;
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
            border: 1px solid #1d4ed8 !important;
            color: #ffffff !important;
            font-weight: 950 !important;
            box-shadow: 0 12px 26px rgba(37, 99, 235, 0.24) !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.login-panel-anchor-v2) .stFormSubmitButton > button:hover {
            color: #ffffff !important;
            border-color: #1e40af !important;
            box-shadow: 0 15px 32px rgba(37, 99, 235, 0.30) !important;
        }

        /* Inputs inside login card */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.login-panel-anchor-v2) .stTextInput input {
            min-height: 48px !important;
            border-radius: 13px !important;
            border: 1px solid #dbe3ef !important;
            background: #ffffff !important;
            color: #07112f !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.login-panel-anchor-v2) .stTextInput label p {
            color: #07112f !important;
            font-weight: 900 !important;
            font-size: 0.84rem !important;
        }

        @media (max-width: 980px) {
            .login-screen-v2 .login-grid-v2 {
                grid-template-columns: 1fr;
            }

            .login-marketing-panel-v2 {
                min-height: auto;
                padding: 32px;
            }

            div[data-testid="stVerticalBlockBorderWrapper"]:has(.login-panel-anchor-v2) {
                min-height: auto !important;
            }

            div[data-testid="stVerticalBlockBorderWrapper"]:has(.login-panel-anchor-v2) > div {
                padding: 30px !important;
            }

            .login-main-title-v2 {
                font-size: 2.6rem;
            }

            .login-feature-grid-v2,
            .workspace-card-row-v2 {
                grid-template-columns: 1fr;
            }

            .login-security-note-v2 {
                position: relative;
                left: auto;
                bottom: auto;
                margin-top: 28px;
            }
        }

        /* ============================
           OPERATIONS DASHBOARD PATCH
           fixes empty white boxes around charts/tables
           ============================ */

        .ops-card-anchor,
        .ops-wide-card-anchor,
        .ops-table-anchor,
        .ops-detail-anchor {
            display: none;
        }

        /* Normal chart card containers */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.ops-card-anchor) {
            background: #ffffff !important;
            border: 1px solid #dbe3ef !important;
            border-radius: 20px !important;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.055) !important;
            padding: 0 !important;
            overflow: hidden !important;
            min-height: 380px !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.ops-card-anchor) > div {
            padding: 18px !important;
        }

        /* Wide chart card containers */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.ops-wide-card-anchor) {
            background: #ffffff !important;
            border: 1px solid #dbe3ef !important;
            border-radius: 20px !important;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.055) !important;
            padding: 0 !important;
            overflow: hidden !important;
            margin-bottom: 18px !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.ops-wide-card-anchor) > div {
            padding: 18px !important;
        }

        /* Table card containers */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.ops-table-anchor) {
            background: #ffffff !important;
            border: 1px solid #dbe3ef !important;
            border-radius: 20px !important;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.055) !important;
            padding: 0 !important;
            overflow: hidden !important;
            margin-bottom: 18px !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.ops-table-anchor) > div {
            padding: 18px !important;
        }

        /* Detail review card containers */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.ops-detail-anchor) {
            background: #ffffff !important;
            border: 1px solid #dbe3ef !important;
            border-radius: 20px !important;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.055) !important;
            padding: 0 !important;
            overflow: hidden !important;
            margin-top: 12px !important;
            margin-bottom: 18px !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.ops-detail-anchor) > div {
            padding: 18px !important;
        }

        /* Chart inner border */
        .ops-page-shell div[data-testid="stVegaLiteChart"],
        .ops-page-shell div[data-testid="stArrowVegaLiteChart"],
        .integration-page-shell div[data-testid="stVegaLiteChart"],
        .integration-page-shell div[data-testid="stArrowVegaLiteChart"],
        .observability-page-shell div[data-testid="stVegaLiteChart"],
        .observability-page-shell div[data-testid="stArrowVegaLiteChart"] {
            background: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 16px !important;
            box-shadow: none !important;
            padding: 10px !important;
            overflow: hidden !important;
        }

        /* Remove extra gap created by charts */
        .ops-page-shell div[data-testid="stVegaLiteChart"] > div,
        .ops-page-shell div[data-testid="stArrowVegaLiteChart"] > div {
            border-radius: 14px !important;
        }

        /* Better chart titles */
        .chart-panel-title {
            font-size: 0.98rem !important;
            font-weight: 950 !important;
            color: #07112f !important;
            letter-spacing: -0.025em !important;
            margin-bottom: 5px !important;
        }

        .chart-panel-subtitle {
            color: #64748b !important;
            font-size: 0.84rem !important;
            line-height: 1.5 !important;
            margin-bottom: 14px !important;
        }

        /* Table header strip */
        .table-action-row {
            background: #f8fafc !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 15px !important;
            padding: 12px 14px !important;
            margin: 4px 0 14px 0 !important;
        }

        .table-meta-text {
            color: #64748b !important;
            font-size: 0.84rem !important;
            line-height: 1.45 !important;
        }

        /* Download button inside table card */
        .ops-page-shell .stDownloadButton > button {
            min-height: 40px !important;
            border-radius: 12px !important;
            background: #ffffff !important;
            color: #07112f !important;
            border: 1px solid #cbd5e1 !important;
            font-weight: 850 !important;
            margin-bottom: 10px !important;
        }

        .ops-page-shell .stDownloadButton > button:hover {
            color: #ff4f16 !important;
            border-color: #ff4f16 !important;
        }

        /* Dataframe polish */
        .ops-page-shell div[data-testid="stDataFrame"] {
            border-radius: 16px !important;
            border: 1px solid #dbe3ef !important;
            overflow: hidden !important;
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.035) !important;
        }

        /* Request selector */
        .request-selector-label {
            color: #334155 !important;
            font-size: 0.84rem !important;
            font-weight: 900 !important;
            margin-top: 16px !important;
            margin-bottom: 7px !important;
        }

        .ops-page-shell div[data-baseweb="select"] {
            border-radius: 13px !important;
        }

        /* Detail review tabs */
        .ops-detail-anchor + div[data-testid="stTabs"] {
            margin-top: 0.4rem !important;
        }

        .ops-page-shell button[data-baseweb="tab"] {
            font-size: 0.82rem !important;
            padding: 11px 10px !important;
        }

        /* ============================
           APPROVAL QUEUE V3 PATCH
           reference-style approval card
           ============================ */

        .approval-v3-anchor,
        .approval-actions-anchor {
            display: none;
        }

        /* Main approval card container */
        .approval-page-shell div[data-testid="stVerticalBlockBorderWrapper"]:has(.approval-v3-anchor) {
            background: #ffffff !important;
            border: 1px solid #dbe3ef !important;
            border-radius: 22px !important;
            box-shadow: 0 18px 42px rgba(15, 23, 42, 0.065) !important;
            padding: 0 !important;
            overflow: hidden !important;
            margin-bottom: 20px !important;
        }

        .approval-page-shell div[data-testid="stVerticalBlockBorderWrapper"]:has(.approval-v3-anchor) > div {
            padding: 0 !important;
        }

        .approval-v3-card {
            padding: 26px 28px 12px 28px;
        }

        .approval-v3-grid {
            display: grid;
            grid-template-columns: minmax(360px, 1.55fr) minmax(140px, 0.55fr) minmax(190px, 0.75fr) minmax(190px, 0.75fr);
            gap: 0;
            align-items: flex-start;
            margin-bottom: 18px;
        }

        .approval-v3-main {
            padding-right: 26px;
        }

        .approval-v3-title-row {
            display: flex;
            align-items: flex-start;
            gap: 13px;
            margin-bottom: 10px;
        }

        .approval-v3-critical-icon {
            width: 36px;
            height: 36px;
            border-radius: 999px;
            background: #fef2f2;
            color: #ef4444;
            border: 1px solid #fecaca;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1rem;
            font-weight: 950;
            flex: 0 0 auto;
        }

        .approval-v3-title {
            color: #07112f;
            font-size: 1.15rem;
            font-weight: 950;
            line-height: 1.28;
            letter-spacing: -0.04em;
            margin-top: 2px;
        }

        .approval-v3-summary {
            color: #64748b;
            font-size: 0.92rem;
            line-height: 1.6;
            margin-left: 49px;
            max-width: 720px;
        }

        .approval-v3-stat {
            min-height: 86px;
            border-left: 1px solid #e2e8f0;
            padding-left: 24px;
            padding-right: 16px;
        }

        .approval-v3-stat-label {
            color: #64748b;
            font-size: 0.72rem;
            font-weight: 950;
            letter-spacing: 0.075em;
            text-transform: uppercase;
            margin-bottom: 9px;
        }

        .approval-v3-stat-value {
            color: #07112f;
            font-size: 1.04rem;
            font-weight: 950;
            line-height: 1.25;
            letter-spacing: -0.025em;
            word-break: break-word;
        }

        .approval-v3-stat-value.high {
            color: #dc2626;
        }

        .approval-v3-stat-value.queue {
            color: #07112f;
        }

        .approval-v3-stat-value.team {
            color: #07112f;
        }

        .approval-v3-badge-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 8px 0 18px 49px;
        }

        .approval-v3-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            border-radius: 999px;
            padding: 7px 12px;
            font-size: 0.76rem;
            font-weight: 950;
            border: 1px solid transparent;
            white-space: nowrap;
        }

        .approval-v3-badge.danger {
            background: #fef2f2;
            color: #b91c1c;
            border-color: #fecaca;
        }

        .approval-v3-badge.warning {
            background: #fff7ed;
            color: #c2410c;
            border-color: #fed7aa;
        }

        .approval-v3-badge.purple {
            background: #f5f3ff;
            color: #6d28d9;
            border-color: #ddd6fe;
        }

        .approval-v3-badge.success {
            background: #ecfdf5;
            color: #047857;
            border-color: #bbf7d0;
        }

        .approval-v3-reason {
            display: grid;
            grid-template-columns: 38px 1fr;
            gap: 13px;
            align-items: flex-start;
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            border-left: 4px solid #2563eb;
            border-radius: 16px;
            padding: 15px 17px;
            margin: 16px 0 18px 0;
        }

        .approval-v3-reason-icon {
            width: 32px;
            height: 32px;
            border-radius: 11px;
            background: #dbeafe;
            color: #1d4ed8;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 950;
        }

        .approval-v3-reason-title {
            color: #1d4ed8;
            font-size: 0.76rem;
            font-weight: 950;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 4px;
        }

        .approval-v3-reason-text {
            color: #1e3a8a;
            font-size: 0.91rem;
            line-height: 1.55;
            font-weight: 750;
        }

        .approval-v3-meta-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 14px;
            flex-wrap: wrap;
            border-top: 1px solid #e2e8f0;
            padding-top: 15px;
            color: #64748b;
            font-size: 0.8rem;
            font-weight: 850;
        }

        .approval-v3-request-pill {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            color: #475569;
            border-radius: 999px;
            padding: 8px 12px;
            max-width: 100%;
            word-break: break-word;
        }

        /* Button area inside approval card */
        .approval-page-shell div[data-testid="stVerticalBlockBorderWrapper"]:has(.approval-v3-anchor) .approval-actions-anchor {
            display: none;
        }

        .approval-page-shell div[data-testid="stVerticalBlockBorderWrapper"]:has(.approval-v3-anchor) div[data-testid="stHorizontalBlock"] {
            padding: 0 28px 24px 28px !important;
            gap: 16px !important;
        }

        .approval-page-shell div[data-testid="stVerticalBlockBorderWrapper"]:has(.approval-v3-anchor) .stButton > button {
            min-height: 48px !important;
            border-radius: 13px !important;
            font-size: 0.9rem !important;
            font-weight: 950 !important;
            box-shadow: none !important;
            margin: 0 !important;
        }

        /* Approve button */
        .approval-page-shell button[data-testid="stBaseButton-primary"],
        .approval-page-shell .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #ff5b1f 0%, #ff4f16 100%) !important;
            color: #ffffff !important;
            border: 1px solid #ff4f16 !important;
            box-shadow: 0 12px 28px rgba(255, 79, 22, 0.22) !important;
        }

        .approval-page-shell button[data-testid="stBaseButton-primary"]:hover,
        .approval-page-shell .stButton > button[kind="primary"]:hover {
            background: linear-gradient(135deg, #ea580c 0%, #ff4f16 100%) !important;
            color: #ffffff !important;
            border-color: #ea580c !important;
            transform: translateY(-1px) !important;
        }

        /* Reject button */
        .approval-page-shell button[data-testid="stBaseButton-secondary"],
        .approval-page-shell .stButton > button[kind="secondary"] {
            background: #ffffff !important;
            color: #ff4f16 !important;
            border: 1px solid #fdba74 !important;
        }

        .approval-page-shell button[data-testid="stBaseButton-secondary"]:hover,
        .approval-page-shell .stButton > button[kind="secondary"]:hover {
            background: #fff7ed !important;
            color: #ea580c !important;
            border-color: #ff4f16 !important;
            transform: translateY(-1px) !important;
        }

        @media (max-width: 1100px) {
            .approval-v3-grid {
                grid-template-columns: 1fr;
                gap: 16px;
            }

            .approval-v3-stat {
                border-left: 0;
                border-top: 1px solid #e2e8f0;
                padding-left: 0;
                padding-top: 15px;
            }

            .approval-v3-summary,
            .approval-v3-badge-row {
                margin-left: 0;
            }

            .approval-page-shell div[data-testid="stVerticalBlockBorderWrapper"]:has(.approval-v3-anchor) div[data-testid="stHorizontalBlock"] {
                padding-left: 22px !important;
                padding-right: 22px !important;
            }
        }

        /* ============================
           OPERATIONS DASHBOARD V3 FIX
           Fix empty chart boxes + cleaner borders
           ============================ */

        .ops-card-anchor,
        .ops-wide-chart-anchor,
        .ops-table-anchor,
        .ops-detail-anchor {
            display: none;
        }

        /* Distribution chart cards */
        .ops-page-shell div[data-testid="stVerticalBlockBorderWrapper"]:has(.ops-card-anchor) {
            background: #ffffff !important;
            border: 1px solid #dbe3ef !important;
            border-radius: 20px !important;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.055) !important;
            padding: 0 !important;
            overflow: hidden !important;
            margin-bottom: 18px !important;
        }

        .ops-page-shell div[data-testid="stVerticalBlockBorderWrapper"]:has(.ops-card-anchor) > div {
            padding: 18px !important;
        }

        /* Wide latency card */
        .ops-page-shell div[data-testid="stVerticalBlockBorderWrapper"]:has(.ops-wide-chart-anchor) {
            background: #ffffff !important;
            border: 1px solid #dbe3ef !important;
            border-radius: 20px !important;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.055) !important;
            padding: 0 !important;
            overflow: hidden !important;
            margin-bottom: 20px !important;
        }

        .ops-page-shell div[data-testid="stVerticalBlockBorderWrapper"]:has(.ops-wide-chart-anchor) > div {
            padding: 18px !important;
        }

        /* Recent records table card */
        .ops-page-shell div[data-testid="stVerticalBlockBorderWrapper"]:has(.ops-table-anchor) {
            background: #ffffff !important;
            border: 1px solid #dbe3ef !important;
            border-radius: 20px !important;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.055) !important;
            padding: 0 !important;
            overflow: hidden !important;
            margin-bottom: 20px !important;
        }

        .ops-page-shell div[data-testid="stVerticalBlockBorderWrapper"]:has(.ops-table-anchor) > div {
            padding: 18px !important;
        }

        /* Detailed request review card */
        .ops-page-shell div[data-testid="stVerticalBlockBorderWrapper"]:has(.ops-detail-anchor) {
            background: #ffffff !important;
            border: 1px solid #dbe3ef !important;
            border-radius: 20px !important;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.055) !important;
            padding: 0 !important;
            overflow: hidden !important;
            margin-top: 12px !important;
            margin-bottom: 20px !important;
        }

        .ops-page-shell div[data-testid="stVerticalBlockBorderWrapper"]:has(.ops-detail-anchor) > div {
            padding: 18px !important;
        }

        /* Remove duplicate border look inside chart areas */
        .ops-page-shell div[data-testid="stVegaLiteChart"],
        .ops-page-shell div[data-testid="stArrowVegaLiteChart"] {
            background: #ffffff !important;
            border: 1px solid #eef2f7 !important;
            border-radius: 16px !important;
            box-shadow: none !important;
            padding: 10px !important;
        }

        /* Better chart title spacing */
        .ops-page-shell .chart-panel-title {
            font-size: 0.98rem !important;
            font-weight: 950 !important;
            color: #07112f !important;
            margin-bottom: 5px !important;
        }

        .ops-page-shell .chart-panel-subtitle {
            color: #64748b !important;
            font-size: 0.84rem !important;
            line-height: 1.5 !important;
            margin-bottom: 14px !important;
        }

        /* Cleaner dataframe inside operations */
        .ops-page-shell div[data-testid="stDataFrame"] {
            border-radius: 15px !important;
            border: 1px solid #dbe3ef !important;
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.035) !important;
            overflow: hidden !important;
        }

        /* ============================
           APPROVAL QUEUE V3
           Clean approval card like target UI
           ============================ */

        .approval-v3-anchor {
            display: none;
        }

        /* Only approval ticket containers */
        .approval-page-shell div[data-testid="stVerticalBlockBorderWrapper"]:has(.approval-v3-anchor) {
            background: #ffffff !important;
            border: 1px solid #dbe3ef !important;
            border-radius: 22px !important;
            box-shadow: 0 18px 42px rgba(15, 23, 42, 0.075) !important;
            padding: 0 !important;
            overflow: hidden !important;
            margin-bottom: 22px !important;
        }

        .approval-page-shell div[data-testid="stVerticalBlockBorderWrapper"]:has(.approval-v3-anchor) > div {
            padding: 0 !important;
        }

        .approval-ticket-card {
            padding: 24px 26px 14px 26px !important;
        }

        .approval-ticket-grid {
            display: grid !important;
            grid-template-columns: minmax(0, 1.45fr) 0.55fr 0.72fr 0.72fr !important;
            gap: 0 !important;
            align-items: flex-start !important;
            margin-bottom: 16px !important;
        }

        .approval-main-info {
            padding-right: 26px !important;
        }

        .approval-ticket-title-row {
            display: grid !important;
            grid-template-columns: 38px 1fr !important;
            gap: 14px !important;
            align-items: flex-start !important;
            margin-bottom: 10px !important;
        }

        .approval-critical-icon {
            width: 36px !important;
            height: 36px !important;
            border-radius: 999px !important;
            background: #fef2f2 !important;
            color: #ef4444 !important;
            border: 1px solid #fecaca !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            font-weight: 950 !important;
            font-size: 1rem !important;
        }

        .approval-title {
            color: #07112f !important;
            font-size: 1.08rem !important;
            font-weight: 950 !important;
            line-height: 1.3 !important;
            letter-spacing: -0.035em !important;
            margin: 2px 0 0 0 !important;
        }

        .approval-summary {
            color: #64748b !important;
            font-size: 0.9rem !important;
            line-height: 1.58 !important;
            margin-left: 52px !important;
            max-width: 650px !important;
        }

        .approval-stat-cell {
            min-height: 82px !important;
            border-left: 1px solid #e2e8f0 !important;
            padding-left: 22px !important;
            padding-right: 16px !important;
        }

        .approval-stat-label {
            color: #64748b !important;
            font-size: 0.7rem !important;
            font-weight: 950 !important;
            letter-spacing: 0.075em !important;
            text-transform: uppercase !important;
            margin-bottom: 10px !important;
        }

        .approval-stat-value {
            color: #07112f !important;
            font-size: 1rem !important;
            font-weight: 950 !important;
            line-height: 1.28 !important;
        }

        .approval-stat-value.high {
            color: #dc2626 !important;
        }

        .approval-badge-row {
            display: flex !important;
            align-items: center !important;
            flex-wrap: wrap !important;
            gap: 9px !important;
            margin: 12px 0 16px 52px !important;
        }

        .approval-soft-badge {
            display: inline-flex !important;
            align-items: center !important;
            gap: 6px !important;
            border-radius: 999px !important;
            padding: 8px 13px !important;
            font-size: 0.76rem !important;
            font-weight: 950 !important;
            border: 1px solid transparent !important;
            white-space: nowrap !important;
        }

        .approval-soft-badge.danger {
            background: #fef2f2 !important;
            color: #b91c1c !important;
            border-color: #fecaca !important;
        }

        .approval-soft-badge.warning {
            background: #fff7ed !important;
            color: #c2410c !important;
            border-color: #fed7aa !important;
        }

        .approval-soft-badge.purple {
            background: #f5f3ff !important;
            color: #6d28d9 !important;
            border-color: #ddd6fe !important;
        }

        .approval-soft-badge.success {
            background: #ecfdf5 !important;
            color: #047857 !important;
            border-color: #bbf7d0 !important;
        }

        .approval-reason-strip {
            display: grid !important;
            grid-template-columns: 38px 1fr !important;
            gap: 14px !important;
            align-items: flex-start !important;
            background: #eff6ff !important;
            border: 1px solid #bfdbfe !important;
            border-left: 4px solid #2563eb !important;
            border-radius: 16px !important;
            padding: 15px 17px !important;
            margin: 16px 0 16px 0 !important;
        }

        .approval-reason-strip-icon {
            width: 32px !important;
            height: 32px !important;
            border-radius: 11px !important;
            background: #dbeafe !important;
            color: #1d4ed8 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            font-weight: 950 !important;
        }

        .approval-reason-strip-title {
            color: #1d4ed8 !important;
            font-size: 0.74rem !important;
            font-weight: 950 !important;
            letter-spacing: 0.08em !important;
            text-transform: uppercase !important;
            margin-bottom: 5px !important;
        }

        .approval-reason-strip-text {
            color: #1e3a8a !important;
            font-size: 0.9rem !important;
            line-height: 1.55 !important;
            font-weight: 800 !important;
        }

        .approval-meta-row {
            display: flex !important;
            justify-content: space-between !important;
            align-items: center !important;
            gap: 14px !important;
            flex-wrap: wrap !important;
            border-top: 1px solid #e2e8f0 !important;
            padding-top: 14px !important;
            color: #64748b !important;
            font-size: 0.8rem !important;
            font-weight: 850 !important;
        }

        .approval-request-pill {
            display: inline-flex !important;
            align-items: center !important;
            gap: 7px !important;
            background: #f8fafc !important;
            border: 1px solid #e2e8f0 !important;
            color: #475569 !important;
            border-radius: 999px !important;
            padding: 8px 12px !important;
            max-width: 100% !important;
            word-break: break-word !important;
        }

        /* Approval action buttons */
        .approval-page-shell .stButton > button {
            min-height: 48px !important;
            border-radius: 13px !important;
            font-weight: 950 !important;
            font-size: 0.92rem !important;
            box-shadow: none !important;
            margin: 0 0 18px 0 !important;
        }

        /* Approve button */
        .approval-page-shell button[data-testid="stBaseButton-primary"],
        .approval-page-shell .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%) !important;
            color: #ffffff !important;
            border: 1px solid #1d4ed8 !important;
            box-shadow: 0 12px 28px rgba(37, 99, 235, 0.22) !important;
        }

        .approval-page-shell button[data-testid="stBaseButton-primary"]:hover,
        .approval-page-shell .stButton > button[kind="primary"]:hover {
            background: linear-gradient(135deg, #1e40af 0%, #2563eb 100%) !important;
            color: #ffffff !important;
            border-color: #1e40af !important;
            transform: translateY(-1px) !important;
        }

        /* Reject button */
        .approval-page-shell button[data-testid="stBaseButton-secondary"],
        .approval-page-shell .stButton > button[kind="secondary"] {
            background: #ffffff !important;
            color: #dc2626 !important;
            border: 1px solid #f87171 !important;
        }

        .approval-page-shell button[data-testid="stBaseButton-secondary"]:hover,
        .approval-page-shell .stButton > button[kind="secondary"]:hover {
            background: #fff7f7 !important;
            color: #b91c1c !important;
            border-color: #dc2626 !important;
            transform: translateY(-1px) !important;
        }

        @media (max-width: 1050px) {
            .approval-ticket-grid {
                grid-template-columns: 1fr !important;
                gap: 14px !important;
            }

            .approval-stat-cell {
                border-left: 0 !important;
                border-top: 1px solid #e2e8f0 !important;
                padding-left: 0 !important;
                padding-top: 14px !important;
            }

            .approval-summary,
            .approval-badge-row {
                margin-left: 0 !important;
            }
        }

        /* ============================
           CHART / TABLE GHOST BOX FIX
           Fixes empty white boxes created by raw HTML wrappers
           ============================ */

        .ops-chart-card,
        .ops-chart-wide-card,
        .ops-table-card,
        .ops-detail-card,
        .benchmark-chart-shell {
            min-height: 0 !important;
            padding: 0 !important;
            margin: 0 !important;
            border: 0 !important;
            box-shadow: none !important;
            background: transparent !important;
        }

        /* Real chart cards generated by Streamlit */
        .ops-page-shell div[data-testid="stVegaLiteChart"],
        .ops-page-shell div[data-testid="stArrowVegaLiteChart"],
        .integration-page-shell div[data-testid="stVegaLiteChart"],
        .integration-page-shell div[data-testid="stArrowVegaLiteChart"],
        .observability-page-shell div[data-testid="stVegaLiteChart"],
        .observability-page-shell div[data-testid="stArrowVegaLiteChart"] {
            background: #ffffff !important;
            border: 1px solid #dbe3ef !important;
            border-radius: 18px !important;
            box-shadow: 0 12px 30px rgba(15, 23, 42, 0.055) !important;
            padding: 12px !important;
            overflow: hidden !important;
        }

        /* Better dataframe/table card feel */
        .ops-page-shell div[data-testid="stDataFrame"],
        .integration-page-shell div[data-testid="stDataFrame"],
        .observability-page-shell div[data-testid="stDataFrame"],
        .project-page-shell div[data-testid="stDataFrame"] {
            background: #ffffff !important;
            border: 1px solid #dbe3ef !important;
            border-radius: 16px !important;
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.045) !important;
            overflow: hidden !important;
        }

        /* Bordered Streamlit containers for benchmark charts */
        .integration-page-shell div[data-testid="stVerticalBlockBorderWrapper"],
        .observability-page-shell div[data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid #dbe3ef !important;
            border-radius: 20px !important;
            background: #ffffff !important;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.055) !important;
        }

        /* Remove too much blank spacing around chart wrappers */
        .ops-page-shell .element-container,
        .integration-page-shell .element-container,
        .observability-page-shell .element-container {
            margin-bottom: 0.35rem !important;
        }

        /* Cleaner chart headings */
        .chart-panel-title {
            color: #07112f !important;
            font-size: 0.98rem !important;
            font-weight: 950 !important;
            letter-spacing: -0.025em !important;
            margin-bottom: 5px !important;
        }

        .chart-panel-subtitle {
            color: #64748b !important;
            font-size: 0.84rem !important;
            line-height: 1.5 !important;
            margin-bottom: 14px !important;
        }

        /* ============================
           LOGIN PAGE V2 - EXACT TARGET UI
           ============================ */

        body:has(.login-v2-page) .main .block-container {
            max-width: 1500px !important;
            padding-top: 2.4rem !important;
            padding-left: 3rem !important;
            padding-right: 3rem !important;
            padding-bottom: 2.5rem !important;
        }

        body:has(.login-v2-page) .stApp {
            background:
                radial-gradient(circle at 18% 18%, rgba(37, 99, 235, 0.18), transparent 34%),
                radial-gradient(circle at 82% 82%, rgba(255, 79, 22, 0.14), transparent 32%),
                linear-gradient(135deg, #020b22 0%, #101849 44%, #2f1e66 72%, #7a2c19 130%) !important;
        }

        .login-v2-page {
            width: 100%;
        }

        .login-v2-left {
            min-height: 780px;
            border-radius: 0;
            padding: 26px 42px 28px 42px;
            color: #ffffff;
            position: relative;
            overflow: hidden;
        }

        .login-v2-left::before {
            content: "";
            position: absolute;
            left: -140px;
            bottom: -110px;
            width: 850px;
            height: 330px;
            opacity: 0.36;
            background:
                repeating-radial-gradient(ellipse at center, rgba(96, 165, 250, 0.42) 0 1px, transparent 1px 15px);
            transform: rotate(-7deg);
        }

        .login-v2-left::after {
            content: "";
            position: absolute;
            right: -120px;
            bottom: -120px;
            width: 620px;
            height: 300px;
            opacity: 0.42;
            background: radial-gradient(circle, rgba(255, 117, 72, 0.55), transparent 62%);
        }

        .login-v2-content {
            position: relative;
            z-index: 1;
        }

        .login-v2-brand {
            display: flex;
            align-items: center;
            gap: 14px;
            margin-bottom: 86px;
        }

        .login-v2-logo {
            width: 48px;
            height: 48px;
            border-radius: 18px;
            background:
                radial-gradient(circle at 30% 30%, #ffffff 0 9%, transparent 10%),
                conic-gradient(from 25deg, #2563eb, #7c3aed, #fb7185, #fb923c, #2563eb);
            box-shadow: 0 16px 34px rgba(96, 165, 250, 0.28);
        }

        .login-v2-brand-text {
            font-size: 1.65rem;
            font-weight: 950;
            letter-spacing: -0.055em;
        }

        .login-v2-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 18px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.10);
            border: 1px solid rgba(255, 255, 255, 0.16);
            color: #93c5fd;
            font-size: 0.8rem;
            font-weight: 950;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            margin-bottom: 28px;
        }

        .login-v2-title {
            max-width: 700px;
            font-size: 3.65rem;
            line-height: 1.16;
            font-weight: 950;
            letter-spacing: -0.07em;
            margin-bottom: 22px;
        }

        .login-v2-gradient {
            background: linear-gradient(90deg, #8b5cf6 0%, #fb7185 45%, #fb923c 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .login-v2-copy {
            max-width: 650px;
            color: rgba(255, 255, 255, 0.78);
            font-size: 1.05rem;
            line-height: 1.62;
            margin-bottom: 34px;
        }

        .login-v2-feature-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            max-width: 650px;
        }

        .login-v2-feature {
            display: grid;
            grid-template-columns: 56px 1fr;
            gap: 16px;
            align-items: center;
            padding: 18px;
            min-height: 112px;
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.14);
            backdrop-filter: blur(8px);
        }

        .login-v2-feature-icon {
            width: 50px;
            height: 50px;
            border-radius: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(37, 99, 235, 0.34);
            border: 1px solid rgba(147, 197, 253, 0.26);
            font-size: 1.25rem;
        }

        .login-v2-feature-title {
            font-size: 0.96rem;
            font-weight: 950;
            margin-bottom: 4px;
        }

        .login-v2-feature-text {
            color: rgba(255, 255, 255, 0.68);
            font-size: 0.82rem;
            line-height: 1.45;
        }

        .login-v2-security {
            position: absolute;
            left: 42px;
            bottom: 28px;
            z-index: 2;
            display: flex;
            align-items: center;
            gap: 9px;
            color: rgba(255, 255, 255, 0.72);
            font-size: 0.86rem;
        }

        /* Right login card - Streamlit bordered container */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.login-right-anchor) {
            min-height: 780px !important;
            border-radius: 30px !important;
            background:radial-gradient(circle at 50% 0%, rgba(37, 99, 235, 0.075), transparent 36%) #ffffff !important;
            border: 1px solid rgba(226, 232, 240, 0.95) !important;
            box-shadow: 0 30px 90px rgba(15, 23, 42, 0.26) !important;
            padding: 0 !important;
            overflow: hidden !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.login-right-anchor) > div {
            padding: 42px 54px 36px 54px !important;
        }

        .login-v2-right-header {
            text-align: center;
            margin-bottom: 26px;
        }

        .login-v2-right-title {
            color: #07112f;
            font-size: 2rem;
            font-weight: 950;
            letter-spacing: -0.055em;
            margin-bottom: 8px;
        }

        .login-v2-right-subtitle {
            color: #64748b;
            font-size: 0.96rem;
        }

        .login-v2-workspace-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 22px;
            margin-bottom: 20px;
        }

        .login-v2-workspace-card {
            min-height: 250px;
            position: relative;
            border-radius: 16px;
            border: 1px solid #dbe3ef;
            background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
            padding: 28px 22px 24px 22px;
            text-align: center;
            transition: all 0.18s ease;
        }

        .login-v2-workspace-card.selected {
            border-color: #2563eb;
            background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%);
            box-shadow: 0 18px 42px rgba(37, 99, 235, 0.14);
        }

        .login-v2-workspace-check {
            position: absolute;
            top: 14px;
            right: 14px;
            width: 25px;
            height: 25px;
            border-radius: 999px;
            background: #2563eb;
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8rem;
            font-weight: 950;
            box-shadow: 0 8px 18px rgba(37, 99, 235, 0.24);
        }

        .login-v2-workspace-icon {
            width: 78px;
            height: 78px;
            border-radius: 999px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 18px auto;
            font-size: 2rem;
            border: 1px solid;
        }

        .login-v2-workspace-icon.admin {
            background: #eff6ff;
            border-color: #bfdbfe;
            color: #2563eb;
        }

        .login-v2-workspace-icon.analyst {
            background: #fff7ed;
            border-color: #fed7aa;
            color: #f97316;
        }

        .login-v2-workspace-title {
            color: #07112f;
            font-size: 1rem;
            font-weight: 950;
            margin-bottom: 24px;
        }

        .login-v2-workspace-text {
            color: #4B5563;
            font-size: 0.9rem;
            line-height: 1.55;
            margin-top: 14px;
        }

        /* Workspace chooser as clean selectable cards */
        body:has(.login-v2-page) div[data-testid="stRadio"] > label {
            display: none !important;
        }

        body:has(.login-v2-page) div[data-testid="stRadio"] div[role="radiogroup"] {
            display: grid !important;
            grid-template-columns: 1fr 1fr !important;
            gap: 22px !important;
            margin-bottom: 22px !important;
        }

        body:has(.login-v2-page) div[data-testid="stRadio"] div[role="radiogroup"] > label {
            position: relative !important;
            min-height: 250px !important;
            border-radius: 18px !important;
            border: 1px solid #dbe3ef !important;
            background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%) !important;
            padding: 28px 22px 24px 22px !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: flex-start !important;
            text-align: center !important;
            gap: 12px !important;
            cursor: pointer !important;
            transition: all 0.18s ease !important;
        }

        /* hide default small radio circle */
        body:has(.login-v2-page) div[data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child {
            display: none !important;
        }

        /* selected card */
        body:has(.login-v2-page) div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) {
            border: 2px solid #2563eb !important;
            background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%) !important;
            box-shadow: 0 18px 42px rgba(37, 99, 235, 0.14) !important;
        }

        /* icon circle */
        body:has(.login-v2-page) div[data-testid="stRadio"] div[role="radiogroup"] > label::before {
            width: 78px !important;
            height: 78px !important;
            border-radius: 999px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            font-size: 2rem !important;
            border: 1px solid !important;
            flex-shrink: 0 !important;
            margin-bottom: 4px !important;
        }

        body:has(.login-v2-page) div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(1)::before {
            content: "🛡";
            background: #eff6ff;
            border-color: #bfdbfe;
            color: #2563eb;
        }

        body:has(.login-v2-page) div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(2)::before {
            content: "👥";
            background: #fff7ed;
            border-color: #fed7aa;
            color: #f97316;
        }

        /* selected check mark */
        body:has(.login-v2-page) div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked)::after {
            content: "✓";
            position: absolute;
            top: 14px;
            right: 14px;
            width: 25px;
            height: 25px;
            border-radius: 999px;
            background: #2563eb;
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8rem;
            font-weight: 950;
            box-shadow: 0 8px 18px rgba(37, 99, 235, 0.24);
        }

        body:has(.login-v2-page) div[data-testid="stRadio"] div[role="radiogroup"] > label p {
            margin: 0 !important;
            color: #07112f !important;
            font-weight: 950 !important;
            line-height: 1.45 !important;
            white-space: normal !important;
        }

        body:has(.login-v2-page) div[data-testid="stRadio"] div[role="radiogroup"] > label small,
        body:has(.login-v2-page) div[data-testid="stRadio"] div[role="radiogroup"] > label [data-testid="stCaptionContainer"] {
            color: #64748b !important;
            font-size: 0.9rem !important;
            line-height: 1.55 !important;
            font-weight: 600 !important;
            max-width: 210px !important;
        }

        /* Divider */
        .login-v2-divider {
            display: flex;
            align-items: center;
            gap: 14px;
            color: #64748b;
            font-size: 0.88rem;
            margin: 18px 0 18px 0;
        }

        .login-v2-divider::before,
        .login-v2-divider::after {
            content: "";
            height: 1px;
            background: #e2e8f0;
            flex: 1;
        }

        /* Login form controls */
        body:has(.login-v2-page) .stTextInput label,
        body:has(.login-v2-page) .stCheckbox label {
            color: #07112f !important;
            font-size: 0.86rem !important;
            font-weight: 900 !important;
        }

        body:has(.login-v2-page) .stTextInput input {
            min-height: 48px !important;
            border-radius: 10px !important;
            border: 1px solid #cfd8e3 !important;
            background: #ffffff !important;
            color: #07112f !important;
            font-size: 0.95rem !important;
        }

        body:has(.login-v2-page) .stTextInput input:focus {
            border-color: #2563eb !important;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12) !important;
        }

        .login-v2-form-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: -4px 0 14px 0;
        }

        .login-v2-forgot {
            color: #2563eb;
            font-size: 0.86rem;
            font-weight: 800;
        }

        body:has(.login-v2-page) .stFormSubmitButton > button {
            width: 100% !important;
            min-height: 52px !important;
            border-radius: 10px !important;
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
            border: 1px solid #1d4ed8 !important;
            color: #ffffff !important;
            font-size: 0.98rem !important;
            font-weight: 950 !important;
            box-shadow: 0 14px 30px rgba(37, 99, 235, 0.28) !important;
        }

        body:has(.login-v2-page) .stFormSubmitButton > button:hover {
            background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%) !important;
            border-color: #1e40af !important;
            color: #ffffff !important;
            transform: translateY(-1px);
        }

        .login-v2-footer {
            text-align: center;
            color: #64748b;
            font-size: 0.82rem;
            line-height: 1.5;
            margin-top: 24px;
        }

        .login-v2-footer a {
            color: #2563eb;
            font-weight: 800;
            text-decoration: none;
        }

        @media (max-width: 1000px) {
            body:has(.login-v2-page) .main .block-container {
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }

            .login-v2-left {
                min-height: auto;
                padding: 30px;
            }

            div[data-testid="stVerticalBlockBorderWrapper"]:has(.login-right-anchor) {
                min-height: auto !important;
            }

            div[data-testid="stVerticalBlockBorderWrapper"]:has(.login-right-anchor) > div {
                padding: 30px !important;
            }

            .login-v2-title {
                font-size: 2.6rem;
            }

            .login-v2-feature-grid,
            .login-v2-workspace-grid {
                grid-template-columns: 1fr;
            }

            .login-v2-security {
                position: relative;
                left: auto;
                bottom: auto;
                margin-top: 24px;
            }
        }

        /* Login right white panel fix */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.login-right-anchor) {
            min-height: 780px !important;
            border-radius: 30px !important;
            background: #ffffff !important;
            border: 1px solid rgba(226, 232, 240, 0.95) !important;
            box-shadow: 0 30px 90px rgba(15, 23, 42, 0.26) !important;
            padding: 0 !important;
            overflow: hidden !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.login-right-anchor) > div {
            padding: 42px 54px 36px 54px !important;
        }
        /* Login security text bottom placement */
        .login-v2-left {
            padding-bottom: 100px !important;
        }

        .login-v2-security {
            position: absolute !important;
            left: 42px !important;
            bottom: 34px !important;
            z-index: 5 !important;
            color: rgba(255, 255, 255, 0.76) !important;
            font-size: 0.88rem !important;
        }

        .login-v2-feature-grid {
            margin-bottom: 90px !important;
        }

        /* Normal app white background */
        .stApp {
            background: #ffffff !important;
        }

        /* Keep gradient only on login page */
        body:has(.login-v2-page) .stApp {
            background:
                radial-gradient(circle at 18% 18%, rgba(37, 99, 235, 0.18), transparent 34%),
                radial-gradient(circle at 82% 82%, rgba(255, 79, 22, 0.14), transparent 32%),
                linear-gradient(135deg, #020b22 0%, #101849 44%, #2f1e66 72%, #7a2c19 130%) !important;
        }
        /* Human correction placeholder color fix */
        .observability-page-shell textarea::placeholder,
        .observability-page-shell input::placeholder {
            color: #94a3b8 !important;
            -webkit-text-fill-color: #94a3b8 !important;
            opacity: 0.65 !important;
        }

        .observability-page-shell textarea::-webkit-input-placeholder,
        .observability-page-shell input::-webkit-input-placeholder {
            color: #94a3b8 !important;
            -webkit-text-fill-color: #94a3b8 !important;
            opacity: 0.65 !important;
        }
        /* =========================================================
           FINAL LOGIN PAGE ONLY PATCH
           Scoped to login page + right login column anchor only
           ========================================================= */

        /* Keep normal app clean after login */
        .stApp {
            background: #ffffff !important;
        }

        /* Login page full-screen gradient */
        body:has(.login-v2-page) .stApp {
            background:
                radial-gradient(circle at 18% 18%, rgba(37, 99, 235, 0.20), transparent 34%),
                radial-gradient(circle at 82% 82%, rgba(255, 79, 22, 0.18), transparent 34%),
                linear-gradient(135deg, #020b22 0%, #11184a 44%, #2e1e65 72%, #762c1a 130%) !important;
        }

        /* Login page content width/spacing */
        body:has(.login-v2-page) .main .block-container {
            max-width: 1500px !important;
            padding-top: 2.2rem !important;
            padding-left: 3rem !important;
            padding-right: 3rem !important;
            padding-bottom: 2.2rem !important;
        }

        /* Left marketing side */
        .login-v2-left {
            min-height: 780px !important;
            position: relative !important;
            overflow: hidden !important;
            padding: 26px 42px 110px 42px !important;
            color: #ffffff !important;
        }

        .login-v2-left::before {
            content: "";
            position: absolute;
            left: -140px;
            bottom: -105px;
            width: 850px;
            height: 330px;
            opacity: 0.36;
            background:
                repeating-radial-gradient(
                    ellipse at center,
                    rgba(96, 165, 250, 0.42) 0 1px,
                    transparent 1px 15px
                );
            transform: rotate(-7deg);
        }

        .login-v2-left::after {
            content: "";
            position: absolute;
            right: -120px;
            bottom: -120px;
            width: 620px;
            height: 300px;
            opacity: 0.42;
            background: radial-gradient(circle, rgba(255, 117, 72, 0.55), transparent 62%);
        }

        .login-v2-content {
            position: relative !important;
            z-index: 2 !important;
        }

        .login-v2-brand {
            display: flex !important;
            align-items: center !important;
            gap: 14px !important;
            margin-bottom: 86px !important;
        }

        .login-v2-logo {
            width: 48px !important;
            height: 48px !important;
            border-radius: 18px !important;
            background:
                radial-gradient(circle at 30% 30%, #ffffff 0 9%, transparent 10%),
                conic-gradient(from 25deg, #2563eb, #7c3aed, #fb7185, #fb923c, #2563eb) !important;
            box-shadow: 0 16px 34px rgba(96, 165, 250, 0.28) !important;
        }

        .login-v2-brand-text {
            font-size: 1.65rem !important;
            font-weight: 950 !important;
            letter-spacing: -0.055em !important;
            color: #ffffff !important;
        }

        .login-v2-pill {
            display: inline-flex !important;
            align-items: center !important;
            gap: 8px !important;
            padding: 10px 18px !important;
            border-radius: 999px !important;
            background: rgba(255, 255, 255, 0.10) !important;
            border: 1px solid rgba(255, 255, 255, 0.16) !important;
            color: #93c5fd !important;
            font-size: 0.8rem !important;
            font-weight: 950 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.07em !important;
            margin-bottom: 28px !important;
        }

        .login-v2-title {
            max-width: 700px !important;
            font-size: 3.65rem !important;
            line-height: 1.16 !important;
            font-weight: 950 !important;
            letter-spacing: -0.07em !important;
            margin-bottom: 22px !important;
            color: #ffffff !important;
        }

        .login-v2-gradient {
            background: linear-gradient(90deg, #8b5cf6 0%, #fb7185 45%, #fb923c 100%) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
        }

        .login-v2-copy {
            max-width: 650px !important;
            color: rgba(255, 255, 255, 0.78) !important;
            font-size: 1.05rem !important;
            line-height: 1.62 !important;
            margin-bottom: 34px !important;
        }

        .login-v2-feature-grid {
            display: grid !important;
            grid-template-columns: 1fr 1fr !important;
            gap: 16px !important;
            max-width: 650px !important;
            margin-bottom: 120px !important;
        }

        .login-v2-feature {
            display: grid !important;
            grid-template-columns: 56px 1fr !important;
            gap: 16px !important;
            align-items: center !important;
            padding: 18px !important;
            min-height: 112px !important;
            border-radius: 18px !important;
            background: rgba(255, 255, 255, 0.08) !important;
            border: 1px solid rgba(255, 255, 255, 0.14) !important;
            backdrop-filter: blur(8px) !important;
        }

        .login-v2-feature-icon {
            width: 50px !important;
            height: 50px !important;
            border-radius: 18px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            background: rgba(37, 99, 235, 0.34) !important;
            border: 1px solid rgba(147, 197, 253, 0.26) !important;
            font-size: 1.25rem !important;
        }

        .login-v2-feature-title {
            font-size: 0.96rem !important;
            font-weight: 950 !important;
            margin-bottom: 4px !important;
            color: #ffffff !important;
        }

        .login-v2-feature-text {
            color: rgba(255, 255, 255, 0.68) !important;
            font-size: 0.82rem !important;
            line-height: 1.45 !important;
        }

        .login-v2-security {
            position: absolute !important;
            left: 42px !important;
            bottom: 34px !important;
            z-index: 5 !important;
            display: flex !important;
            align-items: center !important;
            gap: 9px !important;
            color: rgba(255, 255, 255, 0.76) !important;
            font-size: 0.88rem !important;
        }

        /* Right card: target only the column that contains login-right-anchor */
        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-anchor) {
            min-height: 780px !important;
            background: #ffffff !important;
            background-color: #ffffff !important;
            border: 1px solid rgba(226, 232, 240, 0.98) !important;
            border-radius: 30px !important;
            box-shadow: 0 30px 90px rgba(15, 23, 42, 0.26) !important;
            padding: 42px 54px 36px 54px !important;
            overflow: hidden !important;
            box-sizing: border-box !important;
        }

        /* Remove Streamlit bordered-container look inside right card */
        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-anchor) div[data-testid="stVerticalBlockBorderWrapper"] {
            background: transparent !important;
            background-color: transparent !important;
            border: 0 !important;
            box-shadow: none !important;
            padding: 0 !important;
            min-height: 0 !important;
        }

        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-anchor) div[data-testid="stVerticalBlockBorderWrapper"] > div {
            background: transparent !important;
            background-color: transparent !important;
            padding: 0 !important;
        }

        .login-right-anchor {
            display: none !important;
        }

        /* Right card header */
        .login-v2-right-header {
            text-align: center !important;
            margin-bottom: 26px !important;
        }

        .login-v2-right-title {
            color: #07112f !important;
            -webkit-text-fill-color: #07112f !important;
            font-size: 2rem !important;
            font-weight: 950 !important;
            letter-spacing: -0.055em !important;
            margin-bottom: 8px !important;
        }

        .login-v2-right-subtitle {
            color: #64748b !important;
            font-size: 0.96rem !important;
        }

        /* Workspace radio cards */
        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-anchor) div[data-testid="stRadio"] > label {
            display: none !important;
        }

        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-anchor) div[data-testid="stRadio"] div[role="radiogroup"] {
            display: grid !important;
            grid-template-columns: 1fr 1fr !important;
            gap: 22px !important;
            margin-bottom: 22px !important;
        }

        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-anchor) div[data-testid="stRadio"] div[role="radiogroup"] > label {
            position: relative !important;
            min-height: 250px !important;
            border-radius: 18px !important;
            border: 1px solid #dbe3ef !important;
            background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%) !important;
            padding: 28px 22px 24px 22px !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: flex-start !important;
            text-align: center !important;
            gap: 12px !important;
            cursor: pointer !important;
            transition: all 0.18s ease !important;
        }

        /* Hide default radio circle */
        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-anchor) div[data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child {
            display: none !important;
        }

        /* Selected workspace */
        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-anchor) div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) {
            border: 2px solid #2563eb !important;
            background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%) !important;
            box-shadow: 0 18px 42px rgba(37, 99, 235, 0.14) !important;
        }

        /* Workspace icons */
        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-anchor) div[data-testid="stRadio"] div[role="radiogroup"] > label::before {
            width: 78px !important;
            height: 78px !important;
            border-radius: 999px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            font-size: 2rem !important;
            border: 1px solid !important;
            flex-shrink: 0 !important;
            margin-bottom: 4px !important;
        }

        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-anchor) div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(1)::before {
            content: "🛡";
            background: #eff6ff;
            border-color: #bfdbfe;
            color: #2563eb;
        }

        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-anchor) div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(2)::before {
            content: "👥";
            background: #fff7ed;
            border-color: #fed7aa;
            color: #f97316;
        }

        /* Selected checkmark */
        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-anchor) div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked)::after {
            content: "✓";
            position: absolute;
            top: 14px;
            right: 14px;
            width: 25px;
            height: 25px;
            border-radius: 999px;
            background: #2563eb;
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8rem;
            font-weight: 950;
            box-shadow: 0 8px 18px rgba(37, 99, 235, 0.24);
        }

        /* Workspace text */
        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-anchor) div[data-testid="stRadio"] div[role="radiogroup"] > label p {
            margin: 0 !important;
            color: #07112f !important;
            font-weight: 950 !important;
            line-height: 1.45 !important;
            white-space: normal !important;
        }

        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-anchor) div[data-testid="stRadio"] div[role="radiogroup"] > label small,
        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-anchor) div[data-testid="stRadio"] div[role="radiogroup"] > label [data-testid="stCaptionContainer"] {
            color: #64748b !important;
            font-size: 0.9rem !important;
            line-height: 1.55 !important;
            font-weight: 600 !important;
            max-width: 220px !important;
        }

        /* Divider */
        .login-v2-divider {
            display: flex !important;
            align-items: center !important;
            gap: 14px !important;
            color: #64748b !important;
            font-size: 0.88rem !important;
            margin: 18px 0 18px 0 !important;
        }

        .login-v2-divider::before,
        .login-v2-divider::after {
            content: "" !important;
            height: 1px !important;
            background: #e2e8f0 !important;
            flex: 1 !important;
        }

        /* Inputs inside right card only */
        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-anchor) .stTextInput label,
        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-anchor) .stCheckbox label {
            color: #07112f !important;
            font-size: 0.86rem !important;
            font-weight: 900 !important;
        }

        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-anchor) .stTextInput input {
            min-height: 48px !important;
            border-radius: 10px !important;
            border: 1px solid #cfd8e3 !important;
            background: #ffffff !important;
            background-color: #ffffff !important;
            color: #07112f !important;
            -webkit-text-fill-color: #07112f !important;
            font-size: 0.95rem !important;
        }

        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-anchor) .stTextInput input::placeholder {
            color: #94a3b8 !important;
            -webkit-text-fill-color: #94a3b8 !important;
            opacity: 1 !important;
        }

        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-anchor) .stTextInput input:focus {
            border-color: #2563eb !important;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12) !important;
        }

        .login-v2-forgot {
            width: 100% !important;
            display: block !important;
            text-align: right !important;
            color: #2563eb !important;
            font-size: 0.86rem !important;
            font-weight: 800 !important;
            padding-top: 3px !important;
        }

        /* Login button only inside right card */
        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-anchor) .stFormSubmitButton > button {
            width: 100% !important;
            min-height: 52px !important;
            border-radius: 10px !important;
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
            border: 1px solid #1d4ed8 !important;
            color: #ffffff !important;
            font-size: 0.98rem !important;
            font-weight: 950 !important;
            box-shadow: 0 14px 30px rgba(37, 99, 235, 0.28) !important;
        }

        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-anchor) .stFormSubmitButton > button:hover {
            background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%) !important;
            border-color: #1e40af !important;
            color: #ffffff !important;
            transform: translateY(-1px) !important;
        }

        .login-v2-footer {
            text-align: center !important;
            color: #64748b !important;
            font-size: 0.82rem !important;
            line-height: 1.5 !important;
            margin-top: 24px !important;
        }

        .login-v2-footer a {
            color: #2563eb !important;
            font-weight: 800 !important;
            text-decoration: none !important;
        }

        /* Mobile */
        @media (max-width: 1000px) {
            body:has(.login-v2-page) .main .block-container {
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }

            .login-v2-left {
                min-height: auto !important;
                padding: 30px !important;
            }

            .login-v2-title {
                font-size: 2.6rem !important;
            }

            .login-v2-feature-grid {
                grid-template-columns: 1fr !important;
                margin-bottom: 28px !important;
            }

            .login-v2-security {
                position: relative !important;
                left: auto !important;
                bottom: auto !important;
                margin-top: 24px !important;
            }

            body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-anchor) {
                min-height: auto !important;
                padding: 30px !important;
            }

            body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-anchor) div[data-testid="stRadio"] div[role="radiogroup"] {
                grid-template-columns: 1fr !important;
            }
        }

        /* =========================================================
           FINAL LOGIN PAGE FIX - FULL WHITE RIGHT CARD
           ========================================================= */

        /* Normal app after login stays white */
        .stApp {
            background: #ffffff !important;
        }

        /* Login page background only */
        body:has(.login-v2-page) .stApp {
            background:
                radial-gradient(circle at 18% 18%, rgba(37, 99, 235, 0.20), transparent 34%),
                radial-gradient(circle at 82% 82%, rgba(255, 79, 22, 0.18), transparent 34%),
                linear-gradient(135deg, #020b22 0%, #11184a 44%, #2e1e65 72%, #762c1a 130%) !important;
        }

        /* Login page spacing */
        body:has(.login-v2-page) .main .block-container {
            max-width: 1500px !important;
            padding-top: 2.2rem !important;
            padding-left: 3rem !important;
            padding-right: 3rem !important;
            padding-bottom: 2.2rem !important;
        }

        /* Invisible anchors */
        .login-left-column-anchor,
        .login-right-column-anchor,
        .login-v2-page {
            display: none !important;
        }

        /* Left marketing area */
        .login-v2-left {
            min-height: 780px !important;
            position: relative !important;
            overflow: hidden !important;
            padding: 26px 42px 120px 42px !important;
            color: #ffffff !important;
        }

        .login-v2-left::before {
            content: "";
            position: absolute;
            left: -140px;
            bottom: -105px;
            width: 850px;
            height: 330px;
            opacity: 0.36;
            background:
                repeating-radial-gradient(
                    ellipse at center,
                    rgba(96, 165, 250, 0.42) 0 1px,
                    transparent 1px 15px
                );
            transform: rotate(-7deg);
        }

        .login-v2-left::after {
            content: "";
            position: absolute;
            right: -120px;
            bottom: -120px;
            width: 620px;
            height: 300px;
            opacity: 0.42;
            background: radial-gradient(circle, rgba(255, 117, 72, 0.55), transparent 62%);
        }

        .login-v2-content {
            position: relative !important;
            z-index: 2 !important;
        }

        .login-v2-brand {
            display: flex !important;
            align-items: center !important;
            gap: 14px !important;
            margin-bottom: 86px !important;
        }

        .login-v2-logo {
            width: 48px !important;
            height: 48px !important;
            border-radius: 18px !important;
            background:
                radial-gradient(circle at 30% 30%, #ffffff 0 9%, transparent 10%),
                conic-gradient(from 25deg, #2563eb, #7c3aed, #fb7185, #fb923c, #2563eb) !important;
            box-shadow: 0 16px 34px rgba(96, 165, 250, 0.28) !important;
        }

        .login-v2-brand-text {
            font-size: 1.65rem !important;
            font-weight: 950 !important;
            letter-spacing: -0.055em !important;
            color: #ffffff !important;
        }

        .login-v2-pill {
            display: inline-flex !important;
            align-items: center !important;
            gap: 8px !important;
            padding: 10px 18px !important;
            border-radius: 999px !important;
            background: rgba(255, 255, 255, 0.10) !important;
            border: 1px solid rgba(255, 255, 255, 0.16) !important;
            color: #93c5fd !important;
            font-size: 0.8rem !important;
            font-weight: 950 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.07em !important;
            margin-bottom: 28px !important;
        }

        .login-v2-title {
            max-width: 700px !important;
            font-size: 3.65rem !important;
            line-height: 1.16 !important;
            font-weight: 950 !important;
            letter-spacing: -0.07em !important;
            margin-bottom: 22px !important;
            color: #ffffff !important;
        }

        .login-v2-gradient {
            background: linear-gradient(90deg, #8b5cf6 0%, #fb7185 45%, #fb923c 100%) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
        }

        .login-v2-copy {
            max-width: 650px !important;
            color: rgba(255, 255, 255, 0.78) !important;
            font-size: 1.05rem !important;
            line-height: 1.62 !important;
            margin-bottom: 34px !important;
        }

        .login-v2-feature-grid {
            display: grid !important;
            grid-template-columns: 1fr 1fr !important;
            gap: 16px !important;
            max-width: 650px !important;
            margin-bottom: 130px !important;
        }

        .login-v2-feature {
            display: grid !important;
            grid-template-columns: 56px 1fr !important;
            gap: 16px !important;
            align-items: center !important;
            padding: 18px !important;
            min-height: 112px !important;
            border-radius: 18px !important;
            background: rgba(255, 255, 255, 0.08) !important;
            border: 1px solid rgba(255, 255, 255, 0.14) !important;
            backdrop-filter: blur(8px) !important;
        }

        .login-v2-feature-icon {
            width: 50px !important;
            height: 50px !important;
            border-radius: 18px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            background: rgba(37, 99, 235, 0.34) !important;
            border: 1px solid rgba(147, 197, 253, 0.26) !important;
            font-size: 1.25rem !important;
        }

        .login-v2-feature-title {
            font-size: 0.96rem !important;
            font-weight: 950 !important;
            margin-bottom: 4px !important;
            color: #ffffff !important;
        }

        .login-v2-feature-text {
            color: rgba(255, 255, 255, 0.68) !important;
            font-size: 0.82rem !important;
            line-height: 1.45 !important;
        }

        /* Security note fixed at bottom-left, no overlap */
        .login-v2-security {
            position: absolute !important;
            left: 42px !important;
            bottom: 34px !important;
            z-index: 5 !important;
            display: flex !important;
            align-items: center !important;
            gap: 9px !important;
            color: rgba(255, 255, 255, 0.76) !important;
            font-size: 0.88rem !important;
        }

        /* RIGHT LOGIN COLUMN AS ONE WHITE CARD */
        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-column-anchor),
        body:has(.login-v2-page) div[data-testid="stHorizontalBlock"]:has(.login-left-column-anchor) > div[data-testid="column"]:nth-of-type(2) {
            min-height: 780px !important;
            background: #ffffff !important;
            background-color: #ffffff !important;
            border: 1px solid rgba(226, 232, 240, 0.98) !important;
            border-radius: 30px !important;
            box-shadow: 0 30px 90px rgba(15, 23, 42, 0.26) !important;
            padding: 42px 54px 36px 54px !important;
            overflow: hidden !important;
            box-sizing: border-box !important;
        }

        /* Make inner Streamlit blocks transparent inside the white card */
        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-column-anchor) div[data-testid="stVerticalBlockBorderWrapper"]:not(:has(.login-panel-anchor-v2)),
        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-column-anchor) div[data-testid="element-container"],
        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-column-anchor) div[data-testid="stForm"],
        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-column-anchor) form {
            background: transparent !important;
            background-color: transparent !important;
            border: 0 !important;
            box-shadow: none !important;
            padding: 0 !important;
            min-height: 0 !important;
        }

        /* Right card header */
        .login-v2-right-header {
            text-align: center !important;
            margin-bottom: 26px !important;
        }

        .login-v2-right-title {
            color: #07112f !important;
            -webkit-text-fill-color: #07112f !important;
            font-size: 2rem !important;
            font-weight: 950 !important;
            letter-spacing: -0.055em !important;
            margin-bottom: 8px !important;
        }

        .login-v2-right-subtitle {
            color: #64748b !important;
            font-size: 0.96rem !important;
        }

        /* Workspace radio as clean cards */
        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-column-anchor) div[data-testid="stRadio"] > label {
            display: none !important;
        }

        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-column-anchor) div[data-testid="stRadio"] div[role="radiogroup"] {
            display: grid !important;
            grid-template-columns: 1fr 1fr !important;
            gap: 22px !important;
            margin-bottom: 22px !important;
        }

        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-column-anchor) div[data-testid="stRadio"] div[role="radiogroup"] > label {
            position: relative !important;
            min-height: 250px !important;
            border-radius: 18px !important;
            border: 1px solid #dbe3ef !important;
            background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%) !important;
            padding: 28px 22px 24px 22px !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: flex-start !important;
            text-align: center !important;
            gap: 12px !important;
            cursor: pointer !important;
            transition: all 0.18s ease !important;
        }

        /* Hide default radio circle */
        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-column-anchor) div[data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child {
            display: none !important;
        }

        /* Selected workspace */
        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-column-anchor) div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) {
            border: 2px solid #2563eb !important;
            background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%) !important;
            box-shadow: 0 18px 42px rgba(37, 99, 235, 0.14) !important;
        }

        /* Workspace icon circles */
        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-column-anchor) div[data-testid="stRadio"] div[role="radiogroup"] > label::before {
            width: 78px !important;
            height: 78px !important;
            border-radius: 999px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            font-size: 2rem !important;
            border: 1px solid !important;
            flex-shrink: 0 !important;
            margin-bottom: 4px !important;
        }

        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-column-anchor) div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(1)::before {
            content: "🛡";
            background: #eff6ff;
            border-color: #bfdbfe;
            color: #2563eb;
        }

        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-column-anchor) div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-child(2)::before {
            content: "👥";
            background: #fff7ed;
            border-color: #fed7aa;
            color: #f97316;
        }

        /* Selected check mark */
        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-column-anchor) div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked)::after {
            content: "✓";
            position: absolute;
            top: 14px;
            right: 14px;
            width: 25px;
            height: 25px;
            border-radius: 999px;
            background: #2563eb;
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8rem;
            font-weight: 950;
            box-shadow: 0 8px 18px rgba(37, 99, 235, 0.24);
        }

        /* Workspace text */
        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-column-anchor) div[data-testid="stRadio"] div[role="radiogroup"] > label p {
            margin: 0 !important;
            color: #07112f !important;
            font-weight: 950 !important;
            line-height: 1.45 !important;
            white-space: normal !important;
        }

        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-column-anchor) div[data-testid="stRadio"] div[role="radiogroup"] > label small,
        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-column-anchor) div[data-testid="stRadio"] div[role="radiogroup"] > label [data-testid="stCaptionContainer"] {
            color: #64748b !important;
            font-size: 0.9rem !important;
            line-height: 1.55 !important;
            font-weight: 600 !important;
            max-width: 220px !important;
        }

        /* Divider */
        .login-v2-divider {
            display: flex !important;
            align-items: center !important;
            gap: 14px !important;
            color: #64748b !important;
            font-size: 0.88rem !important;
            margin: 18px 0 18px 0 !important;
        }

        .login-v2-divider::before,
        .login-v2-divider::after {
            content: "" !important;
            height: 1px !important;
            background: #e2e8f0 !important;
            flex: 1 !important;
        }

        /* Inputs inside login card */
        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-column-anchor) .stTextInput label,
        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-column-anchor) .stCheckbox label {
            color: #07112f !important;
            font-size: 0.86rem !important;
            font-weight: 900 !important;
        }

        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-column-anchor) .stTextInput input {
            min-height: 48px !important;
            border-radius: 10px !important;
            border: 1px solid #cfd8e3 !important;
            background: #ffffff !important;
            background-color: #ffffff !important;
            color: #07112f !important;
            -webkit-text-fill-color: #07112f !important;
            font-size: 0.95rem !important;
        }

        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-column-anchor) .stTextInput input::placeholder {
            color: #94a3b8 !important;
            -webkit-text-fill-color: #94a3b8 !important;
            opacity: 1 !important;
        }

        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-column-anchor) .stTextInput input:focus {
            border-color: #2563eb !important;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12) !important;
        }

        .login-v2-forgot {
            width: 100% !important;
            display: block !important;
            text-align: right !important;
            color: #2563eb !important;
            font-size: 0.86rem !important;
            font-weight: 800 !important;
            padding-top: 3px !important;
        }

        /* Login button */
        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-column-anchor) .stFormSubmitButton > button {
            width: 100% !important;
            min-height: 52px !important;
            border-radius: 10px !important;
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
            border: 1px solid #1d4ed8 !important;
            color: #ffffff !important;
            font-size: 0.98rem !important;
            font-weight: 950 !important;
            box-shadow: 0 14px 30px rgba(37, 99, 235, 0.28) !important;
        }

        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-column-anchor) .stFormSubmitButton > button:hover {
            background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%) !important;
            border-color: #1e40af !important;
            color: #ffffff !important;
            transform: translateY(-1px) !important;
        }

        .login-v2-footer {
            text-align: center !important;
            color: #64748b !important;
            font-size: 0.82rem !important;
            line-height: 1.5 !important;
            margin-top: 24px !important;
        }

        .login-v2-footer a {
            color: #2563eb !important;
            font-weight: 800 !important;
            text-decoration: none !important;
        }

        /* Mobile */
        @media (max-width: 1000px) {
            body:has(.login-v2-page) .main .block-container {
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }

            .login-v2-left {
                min-height: auto !important;
                padding: 30px !important;
            }

            .login-v2-title {
                font-size: 2.6rem !important;
            }

            .login-v2-feature-grid {
                grid-template-columns: 1fr !important;
                margin-bottom: 28px !important;
            }

            .login-v2-security {
                position: relative !important;
                left: auto !important;
                bottom: auto !important;
                margin-top: 24px !important;
            }

            body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-column-anchor) {
                min-height: auto !important;
                padding: 30px !important;
            }

            body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-column-anchor) div[data-testid="stRadio"] div[role="radiogroup"] {
                grid-template-columns: 1fr !important;
            }
        }

        /* FORCE RIGHT LOGIN COLUMN TO BE THE WHITE CARD */
        body:has(.login-v2-page) div[data-testid="stHorizontalBlock"]:has(.login-right-column-anchor) > div:nth-of-type(2),
        body:has(.login-v2-page) div[data-testid="stHorizontalBlock"]:has(.login-left-column-anchor) > div:nth-of-type(2),
        body:has(.login-v2-page) div[data-testid="column"]:has(.login-right-column-anchor) {
            min-height: 780px !important;
            background: #ffffff !important;
            background-color: #ffffff !important;
            border: 1px solid rgba(226, 232, 240, 0.98) !important;
            border-radius: 30px !important;
            box-shadow: 0 30px 90px rgba(15, 23, 42, 0.26) !important;
            padding: 42px 54px 36px 54px !important;
            overflow: hidden !important;
            box-sizing: border-box !important;
        }

        /* Remove dark/transparent wrapper effects inside the right card */
        body:has(.login-v2-page) div[data-testid="stHorizontalBlock"]:has(.login-right-column-anchor) > div:nth-of-type(2) div[data-testid="stVerticalBlock"],
        body:has(.login-v2-page) div[data-testid="stHorizontalBlock"]:has(.login-right-column-anchor) > div:nth-of-type(2) div[data-testid="element-container"],
        body:has(.login-v2-page) div[data-testid="stHorizontalBlock"]:has(.login-right-column-anchor) > div:nth-of-type(2) div[data-testid="stForm"],
        body:has(.login-v2-page) div[data-testid="stHorizontalBlock"]:has(.login-right-column-anchor) > div:nth-of-type(2) form {
            background: transparent !important;
            background-color: transparent !important;
            border: 0 !important;
            box-shadow: none !important;
        }

        /* Make sure heading stays dark on white */
        body:has(.login-v2-page) .login-v2-right-title {
            color: #07112f !important;
            -webkit-text-fill-color: #07112f !important;
        }

        body:has(.login-v2-page) .login-v2-right-subtitle {
            color: #64748b !important;
        }

        /* Keep login button blue, not orange */
        body:has(.login-v2-page) .stFormSubmitButton > button {
            width: 100% !important;
            min-height: 52px !important;
            border-radius: 10px !important;
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
            border: 1px solid #1d4ed8 !important;
            color: #ffffff !important;
            font-weight: 950 !important;
            box-shadow: 0 14px 30px rgba(37, 99, 235, 0.28) !important;
        }

        /* =========================================================
           FIX: Move security note to real bottom-left of login page
           ========================================================= */

        /* Make the full left panel the positioning parent */
        body:has(.login-v2-page) .login-v2-left {
            position: relative !important;
            min-height: 780px !important;
            padding-bottom: 120px !important;
        }

        /* Do NOT let inner content become the positioning parent */
        body:has(.login-v2-page) .login-v2-content {
            position: static !important;
            z-index: auto !important;
        }

        /* Keep normal left content above background graphics */
        body:has(.login-v2-page) .login-v2-brand,
        body:has(.login-v2-page) .login-v2-pill,
        body:has(.login-v2-page) .login-v2-title,
        body:has(.login-v2-page) .login-v2-copy,
        body:has(.login-v2-page) .login-v2-feature-grid {
            position: relative !important;
            z-index: 3 !important;
        }

        /* Force security note to bottom-left of the left panel */
        body:has(.login-v2-page) .login-v2-security {
            position: absolute !important;
            left: 42px !important;
            bottom: 34px !important;
            z-index: 5 !important;
            display: flex !important;
            align-items: center !important;
            gap: 9px !important;
            color: rgba(255, 255, 255, 0.76) !important;
            font-size: 0.88rem !important;
            background: transparent !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        /* Give feature cards enough space above the bottom security note */
        body:has(.login-v2-page) .login-v2-feature-grid {
            margin-bottom: 130px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def inject_login_final_fix_css() -> None:
    st.markdown(
        """
        <style>
        /* Hide Streamlit top header only on login page */
        body:has(.login-v2-page) header[data-testid="stHeader"],
        body:has(.login-v2-page) div[data-testid="stToolbar"],
        body:has(.login-v2-page) div[data-testid="stDecoration"],
        body:has(.login-v2-page) #MainMenu,
        body:has(.login-v2-page) footer {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            min-height: 0 !important;
        }

        body:has(.login-v2-page) .main .block-container {
            max-width: 1500px !important;
            padding-top: 1.2rem !important;
            padding-left: 3rem !important;
            padding-right: 3rem !important;
            padding-bottom: 2.2rem !important;
        }

        body:has(.login-v2-page) .stApp {
            background:
                radial-gradient(circle at 18% 18%, rgba(37, 99, 235, 0.20), transparent 34%),
                radial-gradient(circle at 82% 82%, rgba(255, 79, 22, 0.18), transparent 34%),
                linear-gradient(135deg, #020b22 0%, #11184a 44%, #2e1e65 72%, #762c1a 130%) !important;
        }

        .login-v2-left {
            min-height: 780px !important;
            position: relative !important;
            padding: 26px 42px 120px 42px !important;
            overflow: hidden !important;
        }

        .login-v2-feature-grid {
            margin-bottom: 130px !important;
        }

        .login-v2-security {
            position: absolute !important;
            left: 42px !important;
            bottom: 34px !important;
            z-index: 10 !important;
            color: rgba(255, 255, 255, 0.76) !important;
            font-size: 0.88rem !important;
            display: flex !important;
            align-items: center !important;
            gap: 9px !important;
        }

        /* Make the right login column the real white card */
        body:has(.login-v2-page) div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-of-type(2) {
            min-height: 780px !important;
            background: #ffffff !important;
            background-color: #ffffff !important;
            border-radius: 30px !important;
            border: 1px solid rgba(226, 232, 240, 0.98) !important;
            box-shadow: 0 30px 90px rgba(15, 23, 42, 0.26) !important;
            padding: 42px 54px 36px 54px !important;
            overflow: hidden !important;
            box-sizing: border-box !important;
        }

        body:has(.login-v2-page) div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-of-type(2) * {
            color: inherit;
        }

        body:has(.login-v2-page) .login-v2-right-title,
        body:has(.login-v2-page) .workspace-title,
        body:has(.login-v2-page) h1,
        body:has(.login-v2-page) h2,
        body:has(.login-v2-page) h3 {
            color: #07112f !important;
            -webkit-text-fill-color: #07112f !important;
        }

        body:has(.login-v2-page) .login-v2-right-subtitle,
        body:has(.login-v2-page) .workspace-subtitle,
        body:has(.login-v2-page) .login-v2-divider,
        body:has(.login-v2-page) .login-v2-footer {
            color: #64748b !important;
        }

        body:has(.login-v2-page) .stTextInput input {
            background: #ffffff !important;
            color: #07112f !important;
            -webkit-text-fill-color: #07112f !important;
            border: 1px solid #cfd8e3 !important;
            border-radius: 10px !important;
            min-height: 48px !important;
        }

        body:has(.login-v2-page) .stTextInput input::placeholder {
            color: #94a3b8 !important;
            -webkit-text-fill-color: #94a3b8 !important;
            opacity: 1 !important;
        }

        body:has(.login-v2-page) .stFormSubmitButton > button {
            width: 100% !important;
            min-height: 52px !important;
            border-radius: 10px !important;
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
            border: 1px solid #1d4ed8 !important;
            color: #ffffff !important;
            font-weight: 950 !important;
            box-shadow: 0 14px 30px rgba(37, 99, 235, 0.28) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
def get_db_session():
    return SessionLocal()


@st.cache_data(ttl=300, show_spinner=False)
def load_filter_options():
    db = get_db_session()
    try:
        return get_filter_options(db)
    finally:
        db.close()


@st.cache_data(ttl=60, show_spinner=False)
def load_filtered_logs(
    status: str,
    queue: str,
    priority: str,
    search_text: str,
    start_date: date | None,
    end_date: date | None,
    limit: int,
    offset: int = 0,
):
    db = get_db_session()
    try:
        return get_filtered_logs(
            db=db,
            status=status,
            queue=queue,
            priority=priority,
            search_text=search_text,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )
    finally:
        db.close()


@st.cache_data(ttl=60, show_spinner=False)
def load_log_detail(request_id: str):
    db = get_db_session()
    try:
        return get_log_detail(db=db, request_id=request_id)
    finally:
        db.close()


@st.cache_data(ttl=300, show_spinner=False)
def load_benchmark_history(limit: int = 20):
    db = get_db_session()
    try:
        return get_recent_benchmark_runs(db, limit)
    finally:
        db.close()


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def call_triage_api(
    subject: str,
    body: str,
    language_hint: str,
    business_type_hint: str,
    include_draft_response: bool,
    simulate_error: bool = False,
    allow_error_response: bool = False,
) -> dict:
    payload = {
        "subject": subject,
        "body": body,
        "language_hint": language_hint if language_hint.strip() else None,
        "business_type_hint": business_type_hint if business_type_hint.strip() else None,
        "include_draft_response": include_draft_response,
        "simulate_error": simulate_error,
    }

    response = requests.post(
        f"{FASTAPI_BASE_URL}/triage/ticket",
        json=payload,
        timeout=120,
    )

    try:
        data = response.json()
    except Exception:
        data = {"raw_text": response.text}

    if response.status_code >= 400:
        if allow_error_response:
            return {
                "http_status": response.status_code,
                "error_response": data,
            }
        raise RuntimeError(f"API request failed: {data}")

    return data


def run_benchmark_api(sample_size: int, random_seed: int, include_rows: bool = True) -> dict:
    response = requests.post(
        f"{FASTAPI_BASE_URL}/benchmark/run",
        json={
            "sample_size": sample_size,
            "random_seed": random_seed,
            "include_rows": include_rows,
        },
        timeout=600,
    )

    try:
        data = response.json()
    except Exception:
        data = {"raw_text": response.text}

    if response.status_code >= 400:
        raise RuntimeError(f"Benchmark request failed: {data}")

    return data


@st.cache_data(ttl=300, show_spinner=False)
def load_api_config() -> dict:
    response = requests.get(f"{FASTAPI_BASE_URL}/config", timeout=30)
    response.raise_for_status()
    return response.json()

@st.cache_data(ttl=600, show_spinner=False)
def load_outbound_contract_spec() -> dict:
    response = requests.get(
        f"{FASTAPI_BASE_URL}/contracts/outbound-automation/v1",
        timeout=30,
    )
    response.raise_for_status()
    return response.json()

@st.cache_data(ttl=60, show_spinner=False)
def load_observability_summary(hours: int = 24) -> dict:
    response = requests.get(
        f"{FASTAPI_BASE_URL}/observability/summary",
        params={"hours": hours},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()

@st.cache_data(ttl=60, show_spinner=False)
def load_correction_aware_benchmark_summary(days: int = 30) -> dict:
    response = requests.get(
        f"{FASTAPI_BASE_URL}/benchmark/correction-aware-summary",
        params={"days": days},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()

def submit_triage_feedback_api(
    request_id: str,
    queue_correct: bool,
    corrected_queue: str | None = None,
    priority_correct: bool = True,
    corrected_priority: str | None = None,
    intent_correct: bool = True,
    corrected_intent: str | None = None,
    recommended_action_correct: bool = True,
    corrected_recommended_action: str | None = None,
    corrected_by: str | None = None,
    correction_source: str = "human_review",
    notes: str | None = None,
) -> dict:
    payload = {
        "queue_correct": queue_correct,
        "corrected_queue": corrected_queue if corrected_queue and corrected_queue.strip() else None,
        "priority_correct": priority_correct,
        "corrected_priority": corrected_priority if corrected_priority and corrected_priority.strip() else None,
        "intent_correct": intent_correct,
        "corrected_intent": corrected_intent if corrected_intent and corrected_intent.strip() else None,
        "recommended_action_correct": recommended_action_correct,
        "corrected_recommended_action": (
            corrected_recommended_action
            if corrected_recommended_action and corrected_recommended_action.strip()
            else None
        ),
        "corrected_by": corrected_by,
        "correction_source": correction_source,
        "notes": notes if notes and notes.strip() else None,
    }

    response = requests.post(
        f"{FASTAPI_BASE_URL}/triage/logs/{request_id}/feedback",
        json=payload,
        timeout=60,
    )

    data = response.json()

    if response.status_code >= 400:
        raise RuntimeError(data)

    return data

@st.cache_data(ttl=30, show_spinner=False)
def load_policy_audit(limit: int = 50) -> list[dict]:
    response = requests.get(
        f"{FASTAPI_BASE_URL}/policy/audit/recent",
        params={"limit": limit},
        timeout=60,
    )
    response.raise_for_status()
    return response.json().get("items", [])

def invalidate_read_caches() -> None:
    st.cache_data.clear()

@st.cache_data(ttl=10, show_spinner=False)
def load_pending_approvals(limit: int = 50) -> list[dict]:
    response = requests.get(
        f"{FASTAPI_BASE_URL}/approvals/pending",
        params={"limit": limit},
        timeout=60,
    )
    response.raise_for_status()
    return response.json().get("items", [])


def approve_pending_request_api(request_id: str, actor: str, actor_role: str) -> dict:
    response = requests.post(
        f"{FASTAPI_BASE_URL}/approvals/{request_id}/approve",
        json={
            "actor": actor,
            "actor_role": actor_role,
        },
        timeout=120,
    )
    data = response.json()
    if response.status_code >= 400:
        raise RuntimeError(data)
    return data

def reject_pending_request_api(request_id: str, actor: str, actor_role: str) -> dict:
    response = requests.post(
        f"{FASTAPI_BASE_URL}/approvals/{request_id}/reject",
        json={
            "actor": actor,
            "actor_role": actor_role,
        },
        timeout=120,
    )
    data = response.json()
    if response.status_code >= 400:
        raise RuntimeError(data)
    return data


def safe_text(value: Any, fallback: str = "N/A") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def bool_text(value: Any) -> str:
    return "Yes" if bool(value) else "No"

def render_html(markup: str) -> None:
    """
    Render custom HTML without Streamlit Markdown converting it into a code block.
    """
    html = dedent(markup).strip()

    if hasattr(st, "html"):
        st.html(html)
    else:
        compact_html = "\n".join(
            line.strip() for line in html.splitlines() if line.strip()
        )
        st.markdown(compact_html, unsafe_allow_html=True)

def render_badges(items: list[tuple[str, str]]) -> None:
    html = ""
    for label, tone in items:
        html += f'<span class="badge badge-{tone}">{label}</span>'
    st.markdown(html, unsafe_allow_html=True)


def render_metric_card(
    title: str,
    value: str,
    subtitle: str = "",
    icon: str = "",
    tone: str = "blue",
    compact: bool = False,
) -> None:
    icon_html = ""
    if icon:
        icon_html = f'<div class="kpi-icon icon-{escape(tone)}">{escape(icon)}</div>'

    card_class = "kpi-card compact" if compact else "kpi-card"
    value_class = "kpi-value compact" if compact else "kpi-value"

    st.markdown(
        f"""
        <div class="{card_class}">
            <div class="kpi-card-header">
                <div>
                    <div class="kpi-label">{escape(str(title))}</div>
                    <div class="{value_class}">{escape(str(value))}</div>
                </div>
                {icon_html}
            </div>
            <div class="kpi-sub">{escape(str(subtitle))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_info_card(title: str, text: str) -> None:
    st.markdown(
        f"""
        <div class="info-card">
            <div class="info-card-title">{escape(str(title))}</div>
            <div class="info-card-text">{escape(str(text))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_feature_card(icon: str, title: str, text: str, tone: str = "blue") -> None:
    st.markdown(
        f"""
        <div class="feature-card">
            <div class="feature-icon feature-icon-{escape(tone)}">{escape(icon)}</div>
            <div>
                <div class="feature-title">{escape(title)}</div>
                <div class="feature-text">{escape(text)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_result_callout(title: str, text: str, icon: str = "⏳") -> None:
    st.markdown(
        f"""
        <div class="result-callout">
            <div class="result-callout-icon">{escape(icon)}</div>
            <div>
                <div class="result-callout-title">{escape(title)}</div>
                <div class="result-callout-text">{escape(text)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_section_header(title: str, subtitle: str = "", kicker: str | None = None) -> None:
    if kicker:
        st.markdown(f'<div class="section-kicker">{escape(kicker)}</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div class="section-title">{escape(title)}</div>',
        unsafe_allow_html=True,
    )

    if subtitle:
        st.markdown(
            f'<div class="section-subtitle">{escape(subtitle)}</div>',
            unsafe_allow_html=True,
        )


def render_app_header() -> None:
    st.markdown(
        """

        <div class="hero-card">
            <div class="hero-inner">
                <div class="hero-title">ClaudeOps Flow</div>
                <div class="hero-subtitle">
                    AI ticket triage, workflow automation, escalation logic, webhook-ready integrations,
                    operational analytics, benchmark history, and end-to-end demo workflow in one place.
                </div>
                <div class="chip-row">
                    <span class="chip">◎ LLM Triage</span>
                    <span class="chip">▣ FastAPI + PostgreSQL</span>
                    <span class="chip">↗ Streamlit Dashboard</span>
                    <span class="chip">✳ Zapier + Make Ready</span>
                    <span class="chip">▥ Benchmark History</span>
                </div>
            </div>
        </div>

        <div class="top-note">
            <div class="top-note-icon">i</div>
            <div>
                <div class="top-note-title">What this system does</div>
                <div class="top-note-text">
                    ClaudeOps Flow converts unstructured support tickets into structured triage outputs,
                    flags SLA-risk cases, recommends next actions, stores workflow history in PostgreSQL,
                    and prepares automation-ready payloads for downstream operational handling.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_json_panel(title: str, data: Any, expanded: bool = False) -> None:
    with st.expander(title, expanded=expanded):
        if data in (None, "", {}, []):
            st.info("No data available for this section yet.")
        else:
            st.json(data)


def render_empty_state(title: str, text: str) -> None:
    st.markdown(
        f"""
        <div class="panel-card">
            <div class="info-card-title">{escape(title)}</div>
            <div class="info-card-text">{escape(text)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_chart_panel_header(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div>
            <div class="chart-panel-title">{escape(title)}</div>
            <div class="chart-panel-subtitle">{escape(subtitle)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_approval_stat(label: str, value: str, icon: str = "•") -> None:
    st.markdown(
        f"""
        <div class="approval-stat">
            <div class="approval-stat-label">{escape(label)}</div>
            <div class="approval-stat-value">{escape(icon)} {escape(value)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_approval_reason(reason: str) -> None:
    st.markdown(
        f"""
        <div class="approval-reason-box">
            <div class="approval-reason-icon">i</div>
            <div>
                <div class="approval-reason-title">Approval reason</div>
                <div class="approval-reason-text">{escape(reason)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )   

def render_approval_ticket_summary(item: dict) -> None:
    priority = safe_text(item.get("predicted_priority")).title()
    queue = safe_text(item.get("predicted_queue"))
    target_team = safe_text(item.get("automation_target_team"))
    subject = safe_text(item.get("subject"))
    summary = safe_text(item.get("summary"), "No summary available.")
    reason = safe_text(item.get("approval_reason"), "No approval reason available.")
    request_id = safe_text(item.get("request_id"))
    created_at = safe_text(item.get("created_at"))

    sla_badge_tone = "danger" if item.get("sla_risk") else "success"
    review_badge_tone = "warning" if item.get("needs_human_review") else "success"
    priority_class = "high" if priority.lower() == "high" else ""

    render_html(
        f"""
        <div class="approval-v3-anchor"></div>

        <div class="approval-ticket-card">
            <div class="approval-ticket-grid">
                <div class="approval-main-info">
                    <div class="approval-ticket-title-row">
                        <div class="approval-critical-icon">!</div>
                        <div class="approval-title">{escape(subject)}</div>
                    </div>

                    <div class="approval-summary">
                        {escape(summary)}
                    </div>
                </div>

                <div class="approval-stat-cell">
                    <div class="approval-stat-label">Priority</div>
                    <div class="approval-stat-value {priority_class}">⚑ {escape(priority)}</div>
                </div>

                <div class="approval-stat-cell">
                    <div class="approval-stat-label">Queue</div>
                    <div class="approval-stat-value">▣ {escape(queue)}</div>
                </div>

                <div class="approval-stat-cell">
                    <div class="approval-stat-label">Target Team</div>
                    <div class="approval-stat-value">👥 {escape(target_team)}</div>
                </div>
            </div>

            <div class="approval-badge-row">
                <span class="approval-soft-badge {sla_badge_tone}">
                    SLA Risk: {escape(bool_text(item.get("sla_risk")))}
                </span>

                <span class="approval-soft-badge {review_badge_tone}">
                    Human Review: {escape(bool_text(item.get("needs_human_review")))}
                </span>

                <span class="approval-soft-badge purple">
                    Urgency: {escape(safe_text(item.get("automation_urgency_level")))}
                </span>
            </div>

            <div class="approval-reason-strip">
                <div class="approval-reason-strip-icon">i</div>
                <div>
                    <div class="approval-reason-strip-title">Approval reason</div>
                    <div class="approval-reason-strip-text">{escape(reason)}</div>
                </div>
            </div>

            <div class="approval-meta-row">
                <div class="approval-request-pill">Request ID: {escape(request_id)}</div>
                <div>Created: {escape(created_at)}</div>
            </div>
        </div>
        """
    )

def render_integration_status_card(
    title: str,
    value: str,
    subtitle: str,
    icon: str,
    tone: str = "green",
) -> None:
    st.markdown(
        f"""
        <div class="integration-status-card">
            <div>
                <div class="integration-status-top">
                    <div class="integration-status-label">{escape(title)}</div>
                    <div class="integration-status-icon icon-{escape(tone)}">{escape(icon)}</div>
                </div>
                <div class="integration-status-value">{escape(value)}</div>
            </div>
            <div class="integration-status-sub">{escape(subtitle)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
def render_integration_status_card_v2(
    title: str,
    value: str,
    subtitle: str,
    icon: str,
    tone: str = "green",
) -> str:
    return f"""
    <div class="integration-v2-card">
        <div>
            <div class="integration-v2-top">
                <div class="integration-v2-label">{escape(title)}</div>
                <div class="integration-v2-icon icon-{escape(tone)}">{escape(icon)}</div>
            </div>
            <div class="integration-v2-value">{escape(value)}</div>
        </div>
        <div class="integration-v2-subtitle">{escape(subtitle)}</div>
    </div>
    """


def render_contract_metric_card(
    label: str,
    value: str,
    subtitle: str,
    icon: str,
    tone: str = "blue",
) -> str:
    return f"""
    <div class="contract-metric-card">
        <div class="contract-metric-icon icon-{escape(tone)}">{escape(icon)}</div>
        <div class="contract-metric-label">{escape(label)}</div>
        <div class="contract-metric-value">{escape(value)}</div>
        <div class="contract-metric-subtitle">{escape(subtitle)}</div>
    </div>
    """

def render_observability_section(title: str, text: str, right_label: str | None = None) -> None:
    right_html = ""

    if right_label:
        right_html = f'<div class="obs-window-pill">◷ {escape(right_label)}</div>'

    st.markdown(
        f"""
        <div class="obs-section-top">
            <div>
                <div class="obs-section-title">{escape(title)}</div>
                <div class="obs-section-text">{escape(text)}</div>
            </div>
            {right_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_observability_alert(alert_type: str, message: str, severity: str = "medium") -> None:
    severity_key = severity if severity in {"high", "medium", "low"} else "medium"

    icon = "!"
    if severity_key == "low":
        icon = "i"
    elif severity_key == "medium":
        icon = "⚠"

    st.markdown(
        f"""
        <div class="obs-alert-item obs-alert-{escape(severity_key)}">
            <div class="obs-alert-icon">{escape(icon)}</div>
            <div>
                <div class="obs-alert-title">{escape(alert_type)}</div>
                <div class="obs-alert-message">{escape(message)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
def render_obs_section_header_v2(
    number: str,
    title: str,
    text: str,
    badge: str | None = None,
) -> None:
    badge_html = ""

    if badge:
        badge_html = f'<div class="obs-section-badge">◷ {escape(badge)}</div>'

    st.markdown(
        f"""
        <div class="obs-section-heading-row">
            <div class="obs-section-heading-left">
                <div class="obs-section-mini-label">Section {escape(number)}</div>
                <div class="obs-section-heading-title">{escape(title)}</div>
                <div class="obs-section-heading-text">{escape(text)}</div>
            </div>
            {badge_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_obs_intro_panel(selected_window_label: str) -> None:
    st.markdown(
        f"""
        <div class="obs-intro-card-v2">
            <div class="obs-intro-eyebrow">Operated AI monitoring</div>
            <div class="obs-intro-title-v2">Production-style visibility for the ClaudeOps workflow</div>
            <div class="obs-intro-text-v2">
                This page groups runtime health, token usage, cost tracking, drift alerts,
                human correction feedback, benchmark quality, policy audit, and raw trace
                debugging into one monitoring workspace. Current window:
                <strong>{escape(selected_window_label)}</strong>.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_overview_card(icon: str, title: str, text: str, tone: str = "blue") -> None:
    st.markdown(
        f"""
        <div class="overview-card">
            <div class="overview-card-icon icon-{escape(tone)}">{escape(icon)}</div>
            <div class="overview-card-title">{escape(title)}</div>
            <div class="overview-card-text">{escape(text)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_role_pills(items: list[str]) -> None:
    html = '<div class="role-pill-row">'

    for item in items:
        html += f'<span class="role-pill">✓ {escape(item)}</span>'

    html += "</div>"

    st.markdown(html, unsafe_allow_html=True)
def render_project_capability_card(
    icon: str,
    title: str,
    text: str,
    tone: str = "blue",
) -> None:
    st.markdown(
        f"""
        <div class="project-capability-card">
            <div class="project-capability-icon icon-{escape(tone)}">{escape(icon)}</div>
            <div class="project-capability-title">{escape(title)}</div>
            <div class="project-capability-text">{escape(text)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_project_architecture_card(title: str, text: str) -> None:
    st.markdown(
        f"""
        <div class="project-architecture-card">
            <div class="project-architecture-title">{escape(title)}</div>
            <div class="project-architecture-text">{escape(text)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_role_card_v2(
    icon: str,
    title: str,
    text: str,
    capabilities: list[str],
    tone: str = "blue",
) -> None:
    pills_html = '<div class="role-pill-row-v2">'

    for item in capabilities:
        pills_html += f'<span class="role-pill-v2">✓ {escape(item)}</span>'

    pills_html += "</div>"

    st.markdown(
        f"""
        <div class="role-card-v2">
            <div class="role-card-top-v2">
                <div class="role-card-icon-v2 icon-{escape(tone)}">{escape(icon)}</div>
                <div class="role-card-title-v2">{escape(title)}</div>
            </div>
            <div class="role-card-text-v2">{escape(text)}</div>
            {pills_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_sidebar_brand() -> None:
    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="brand-mark"></div>
            <div class="brand-name">ClaudeOps Flow</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_sidebar_role() -> None:
    role = safe_text(st.session_state.user_role)
    username = safe_text(st.session_state.username)

    st.markdown(
        f"""
        <div class="sidebar-user-line">
            <span class="sidebar-icon">👤</span>
            <span>User: {escape(username)}</span>
        </div>
        <div class="sidebar-user-line">
            <span class="sidebar-icon">🛡</span>
            <span>Role: {escape(role)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

def slim_bar_chart(series: pd.Series, key: str, height: int = 250) -> None:
    if series is None or series.empty:
        st.caption("No data available.")
        return

    chart_df = pd.DataFrame(
        {
            "label": series.index.astype(str),
            "value": series.values,
        }
    )

    chart = (
        alt.Chart(chart_df)
        .mark_bar(
            size=34,
            cornerRadiusTopLeft=6,
            cornerRadiusTopRight=6,
            color="#2563eb",
        )
        .encode(
            x=alt.X(
                "label:N",
                sort="-y",
                title=None,
                axis=alt.Axis(
                    labelAngle=-25,
                    labelLimit=130,
                    labelColor="#64748b",
                    labelFontSize=11,
                    title=None,
                ),
                scale=alt.Scale(paddingInner=0.55, paddingOuter=0.25),
            ),
            y=alt.Y(
                "value:Q",
                title=None,
                axis=alt.Axis(
                    grid=True,
                    gridColor="#e5e7eb",
                    labelColor="#64748b",
                    labelFontSize=11,
                ),
            ),
            tooltip=[
                alt.Tooltip("label:N", title="Category"),
                alt.Tooltip("value:Q", title="Count"),
            ],
        )
        .properties(height=height)
        .configure_view(stroke=None)
        .configure_axis(domain=False, tickSize=0)
    )

    st.altair_chart(chart, use_container_width=True, key=key)

def full_width_line_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    key: str,
    height: int = 380,
) -> None:
    if df.empty:
        st.caption("No trend data available.")
        return

    chart = (
        alt.Chart(df)
        .mark_line(
            point=alt.OverlayMarkDef(size=55, filled=True),
            strokeWidth=3,
            color="#2563eb",
        )
        .encode(
            x=alt.X(
                f"{x_col}:T",
                title=None,
                axis=alt.Axis(
                    labelColor="#64748b",
                    labelFontSize=11,
                    grid=False,
                    tickSize=0,
                ),
            ),
            y=alt.Y(
                f"{y_col}:Q",
                title=None,
                axis=alt.Axis(
                    labelColor="#64748b",
                    labelFontSize=11,
                    grid=True,
                    gridColor="#e2e8f0",
                    tickSize=0,
                ),
            ),
            tooltip=[
                alt.Tooltip(f"{x_col}:T", title="Created At"),
                alt.Tooltip(f"{y_col}:Q", title="Latency ms"),
            ],
        )
        .properties(height=height)
        .configure_view(strokeWidth=0)
        .configure_axis(domain=False)
    )

    st.altair_chart(chart, use_container_width=True, key=key)

def humanize_columns(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {
        "request_id": "Request ID",
        "status": "Status",
        "provider": "Provider",
        "model_name": "Model",
        "subject": "Subject",
        "predicted_queue": "Queue",
        "predicted_priority": "Priority",
        "predicted_type": "Type",
        "likely_intent": "Intent",
        "sla_risk": "SLA Risk",
        "confidence": "Confidence",
        "latency_ms": "Latency (ms)",
        "retry_count": "Retry Count",
        "had_retry": "Had Retry",
        "error_type": "Error Type",
        "automation_ready": "Automation Ready",
        "automation_should_escalate": "Escalate",
        "automation_target_team": "Target Team",
        "automation_urgency_level": "Automation Urgency",
        "created_at": "Created At",
        "id": "Log ID",
    }
    return df.rename(columns=mapping)


def compute_dashboard_metrics(df: pd.DataFrame) -> dict:
    total_logs = len(df)
    success_logs = int((df["status"] == "success").sum()) if "status" in df.columns else 0
    success_rate = (success_logs / total_logs * 100) if total_logs else 0.0
    sla_risk_rate = (
        (df["sla_risk"].fillna(False).astype(bool).sum() / total_logs) * 100
        if "sla_risk" in df.columns and total_logs
        else 0.0
    )
    avg_confidence = (
        df["confidence"].dropna().mean()
        if "confidence" in df.columns and not df["confidence"].dropna().empty
        else None
    )
    avg_latency_ms = (
        df["latency_ms"].dropna().mean()
        if "latency_ms" in df.columns and not df["latency_ms"].dropna().empty
        else None
    )
    retry_rate = (
        (df["had_retry"].fillna(False).astype(bool).sum() / total_logs) * 100
        if "had_retry" in df.columns and total_logs
        else 0.0
    )
    escalation_rate = (
        (df["automation_should_escalate"].fillna(False).astype(bool).sum() / total_logs) * 100
        if "automation_should_escalate" in df.columns and total_logs
        else 0.0
    )
    top_queue = (
        df["predicted_queue"].mode().iloc[0]
        if "predicted_queue" in df.columns and df["predicted_queue"].notna().any()
        else "N/A"
    )

    return {
        "total_logs": total_logs,
        "success_rate": success_rate,
        "sla_risk_rate": sla_risk_rate,
        "avg_confidence": avg_confidence,
        "avg_latency_ms": avg_latency_ms,
        "retry_rate": retry_rate,
        "escalation_rate": escalation_rate,
        "top_queue": top_queue,
    }


def build_histogram_series(values: pd.Series, bins: int = 6) -> pd.Series:
    values = pd.to_numeric(values, errors="coerce").dropna()
    if values.empty:
        return pd.Series(dtype="int64")
    bucketed = pd.cut(values, bins=bins)
    counts = bucketed.value_counts().sort_index()
    counts.index = counts.index.astype(str)
    return counts


def authenticate(username: str, password: str) -> str | None:
    if username == DEMO_ADMIN_USERNAME and password == DEMO_ADMIN_PASSWORD:
        return "admin"
    if username == DEMO_ANALYST_USERNAME and password == DEMO_ANALYST_PASSWORD:
        return "ops_analyst"
    return None

def apply_workspace_login_defaults() -> None:
    selected_workspace = st.session_state.get("selected_workspace", "admin")

    if selected_workspace == "admin":
        st.session_state.login_username = DEMO_ADMIN_USERNAME
        st.session_state.login_password = DEMO_ADMIN_PASSWORD
    else:
        st.session_state.login_username = DEMO_ANALYST_USERNAME
        st.session_state.login_password = DEMO_ANALYST_PASSWORD


def render_login_workspace_cards(selected_workspace: str) -> None:
    admin_selected = selected_workspace == "admin"
    analyst_selected = selected_workspace == "ops_analyst"

    admin_check = '<div class="login-v2-workspace-check">✓</div>' if admin_selected else ""
    analyst_check = '<div class="login-v2-workspace-check">✓</div>' if analyst_selected else ""

    admin_class = "login-v2-workspace-card selected" if admin_selected else "login-v2-workspace-card"
    analyst_class = "login-v2-workspace-card selected" if analyst_selected else "login-v2-workspace-card"

    render_html(
        f"""
        <div class="login-v2-right-header">
            <div class="login-v2-right-title">Choose your workspace</div>
            <div class="login-v2-right-subtitle">Select the workspace you want to access.</div>
        </div>

        <div class="login-v2-workspace-grid">
            <div class="{admin_class}">
                {admin_check}
                <div class="login-v2-workspace-icon admin">🛡</div>
                <div class="login-v2-workspace-title">Admin Workspace</div>
                <div class="login-v2-workspace-text">
                    Full access to integrations, benchmarks, policies,
                    approvals, observability, and project overview.
                </div>
            </div>

            <div class="{analyst_class}">
                {analyst_check}
                <div class="login-v2-workspace-icon analyst">👥</div>
                <div class="login-v2-workspace-title">Ops Analyst Workspace</div>
                <div class="login-v2-workspace-text">
                    Operational view for ticket handling, dashboards,
                    approvals, and automation flow.
                </div>
            </div>
        </div>
        """
    )

def render_workspace_option_card(
    workspace_key: str,
    title: str,
    text: str,
    icon: str,
    icon_class: str,
) -> str:
    selected = st.session_state.get("selected_workspace") == workspace_key
    selected_class = "selected" if selected else ""
    check_html = '<div class="workspace-check-v2">✓</div>' if selected else ""

    return f"""
    <div class="workspace-option-card-v2 {selected_class}">
        {check_html}
        <div class="workspace-icon-v2 {escape(icon_class)}">{escape(icon)}</div>
        <div class="workspace-card-title-v2">{escape(title)}</div>
        <div class="workspace-card-text-v2">{escape(text)}</div>
    </div>
    """

inject_custom_css()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "username" not in st.session_state:
    st.session_state.username = None
if "last_submission_result" not in st.session_state:
    st.session_state.last_submission_result = None
if "last_simulation_result" not in st.session_state:
    st.session_state.last_simulation_result = None
if "last_benchmark_result" not in st.session_state:
    st.session_state.last_benchmark_result = None
if "auto_refresh_after_submit" not in st.session_state:
    st.session_state.auto_refresh_after_submit = False
if "selected_workspace" not in st.session_state:
    st.session_state.selected_workspace = "admin"
if "login_username" not in st.session_state:
    st.session_state.login_username = DEMO_ADMIN_USERNAME
if "login_password" not in st.session_state:
    st.session_state.login_password = DEMO_ADMIN_PASSWORD

if not st.session_state.authenticated:
    # Marker only. This lets CSS apply login-only styling without affecting the app after login.
    st.markdown('<div class="login-v2-page"></div>', unsafe_allow_html=True)

    login_left, login_right = st.columns([1.08, 0.92], gap="large")

    with login_left:
        # Important: this anchor is rendered with st.markdown, not render_html,
        # so CSS can reliably detect the left login column.
        st.markdown('<div class="login-left-column-anchor"></div>', unsafe_allow_html=True)

        render_html(
            """
            <div class="login-v2-left">
                <div class="login-v2-content">
                    <div class="login-v2-brand">
                        <div class="login-v2-logo"></div>
                        <div class="login-v2-brand-text">ClaudeOps Flow</div>
                    </div>

                    <div class="login-v2-pill">✦ AI-powered operations</div>

                    <div class="login-v2-title">
                        AI-Powered Support Operations,
                        <span class="login-v2-gradient">Seamlessly.</span>
                    </div>

                    <div class="login-v2-copy">
                        ClaudeOps Flow streamlines ticket triage, escalation, approvals,
                        automation readiness, observability, and benchmark analytics all in one place.
                    </div>

                    <div class="login-v2-feature-grid">
                        <div class="login-v2-feature">
                            <div class="login-v2-feature-icon">👤</div>
                            <div>
                                <div class="login-v2-feature-title">Role-based access</div>
                                <div class="login-v2-feature-text">
                                    Secure and tailored for every team.
                                </div>
                            </div>
                        </div>

                        <div class="login-v2-feature">
                            <div class="login-v2-feature-icon">✅</div>
                            <div>
                                <div class="login-v2-feature-title">Human approval flow</div>
                                <div class="login-v2-feature-text">
                                    Built-in governance with structured approvals.
                                </div>
                            </div>
                        </div>

                        <div class="login-v2-feature">
                            <div class="login-v2-feature-icon">🛡</div>
                            <div>
                                <div class="login-v2-feature-title">Policy audit</div>
                                <div class="login-v2-feature-text">
                                    Ensure compliance with automated policy checks.
                                </div>
                            </div>
                        </div>

                        <div class="login-v2-feature">
                            <div class="login-v2-feature-icon">⚡</div>
                            <div>
                                <div class="login-v2-feature-title">Automation ready</div>
                                <div class="login-v2-feature-text">
                                    Ready for automation at every step.
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="login-v2-security">
                        🔒 Enterprise-grade security & compliance
                    </div>
                </div>
            </div>
            """
        )

    with login_right:
        st.markdown('<div class="login-right-column-anchor"></div>', unsafe_allow_html=True)

        render_html(
            """
            <div class="login-v2-right-header">
                <div class="login-v2-right-title">Choose your workspace</div>
                <div class="login-v2-right-subtitle">Select the workspace you want to access.</div>
            </div>
            """
        )
        selected_workspace = st.radio(
            "Workspace",
            options=["admin", "ops_analyst"],
            key="selected_workspace",
            horizontal=True,
            label_visibility="collapsed",
            captions=[
                "Full access to integrations, benchmarks, policies, approvals, observability, and project overview.",
                "Operational view for ticket handling, dashboards, approvals, and automation flow.",
            ],
            format_func=lambda value: (
                "Admin Workspace" if value == "admin" else "Ops Analyst Workspace"
            ),
            on_change=apply_workspace_login_defaults,
        )
        st.markdown(
            '<div class="login-v2-divider">Login to your selected workspace.</div>',
            unsafe_allow_html=True,
        )
        with st.form("login_form"):
            username = st.text_input(
                "Username",
                placeholder="Enter your username",
                key="login_username",
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="login_password",
            )
            remember_col, forgot_col = st.columns([1, 1])
            with remember_col:
                st.checkbox("Remember me", value=False)
            with forgot_col:
                st.markdown(
                    '<div class="login-v2-forgot">Forgot password?</div>',
                    unsafe_allow_html=True,
                )
            login_btn = st.form_submit_button("Log in", use_container_width=True)
        if login_btn:
            role = authenticate(username, password)
            if role:
                st.session_state.authenticated = True
                st.session_state.user_role = role
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid username or password.")
        render_html(
            """
            <div class="login-v2-footer">
                By continuing, you agree to our
                <a href="#">Security Policy</a> and
                <a href="#">Terms of Use</a>.
            </div>
            """
        )

        st.stop()

render_app_header()

with st.sidebar:
    render_sidebar_brand()

    st.markdown('<div class="sidebar-section-label">Session</div>', unsafe_allow_html=True)
    render_sidebar_role()

    if st.button("↪ Logout", use_container_width=True):
        for key in [
            "authenticated",
            "user_role",
            "username",
            "last_submission_result",
            "last_simulation_result",
            "last_benchmark_result",
            "auto_refresh_after_submit",
            "last_policy_decisions",
            "last_approval_message",
        ]:
            st.session_state.pop(key, None)
        st.rerun()

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section-label">Filters</div>', unsafe_allow_html=True)

    filter_options = load_filter_options()
    status_filter = st.selectbox("Status", ["All"] + filter_options["statuses"], index=0)
    queue_filter = st.selectbox("Queue", ["All"] + filter_options["queues"], index=0)
    priority_filter = st.selectbox("Priority", ["All"] + filter_options["priorities"], index=0)
    search_filter = st.text_input("Search by Request ID or Subject", value="")

    if filter_options["min_created_at"] and filter_options["max_created_at"]:
        date_range = st.date_input(
            "Created Date Range",
            value=(filter_options["min_created_at"], filter_options["max_created_at"]),
            min_value=filter_options["min_created_at"],
            max_value=filter_options["max_created_at"],
        )
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date, end_date = None, None
    else:
        start_date, end_date = None, None

    page_size = st.selectbox(
        "Rows per page",
        options=[25, 50, 100, 200],
        index=1,
    )

    page_number = st.number_input(
        "Page number",
        min_value=1,
        value=1,
        step=1,
    )

    limit_filter = int(page_size)
    offset_filter = (int(page_number) - 1) * int(page_size)

    refresh = st.button("Refresh Dashboard")

tab_names = ["✎ Submit Ticket", "▦ Operations Dashboard"]

if st.session_state.user_role in {"admin", "ops_analyst"}:
    tab_names.append("♙ Approval Queue")

if st.session_state.user_role == "admin":
    tab_names.extend(
        [
            "✣ Integrations & Benchmark",
            "◉ Observability",
        ]
    )

if st.session_state.user_role in {"admin", "ops_analyst"}:
    tab_names.append("▣ Project Overview")

tabs = st.tabs(tab_names)

project_overview_tab_index = tab_names.index("▣ Project Overview")

with tabs[0]:
    st.markdown('<div class="submit-page-shell">', unsafe_allow_html=True)

    render_section_header(
        "Live Ticket Submission",
        "Enter a support request, call the FastAPI triage endpoint, and instantly review the AI result.",
    )

    left_col, right_col = st.columns([1.55, 1], gap="large")

    with left_col:
        with st.container(border=True):
            st.markdown(
                """
                <div class="submit-form-intro">
                    <div class="submit-form-title">Submit a support ticket</div>
                    <div class="submit-form-subtitle">
                        This form sends the ticket to your FastAPI backend, stores the result in PostgreSQL,
                        and returns structured triage, routing, priority, SLA risk, and automation readiness.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.form("ticket_submission_form", clear_on_submit=False):
                subject = st.text_input(
                    "Ticket Subject",
                    value="Critical payment issue affecting customer orders",
                    placeholder="Example: Critical payment issue affecting customer orders",
                )

                body = st.text_area(
                    "Ticket Description",
                    value=(
                        "Several customers are unable to complete checkout since this morning. "
                        "Payment failures are increasing and support volume is rising. "
                        "Please investigate urgently and advise on next steps."
                    ),
                    height=170,
                    placeholder="Describe the customer issue, urgency, impact, and any useful context.",
                )

                form_col1, form_col2 = st.columns(2)

                with form_col1:
                    language_hint = st.selectbox(
                        "Language",
                        options=["en", "de", "fr", "es", "pt"],
                        index=0,
                    )

                with form_col2:
                    business_type_hint = st.text_input(
                        "Business Context",
                        value="Tech Online Store",
                        placeholder="Example: Tech Online Store",
                    )

                include_draft_response = st.checkbox(
                    "Generate Draft Response",
                    value=True,
                )

                submit_button = st.form_submit_button(
                    "Run AI Triage",
                    use_container_width=True,
                )

        if submit_button:
            if not subject.strip():
                st.error("Subject is required.")
            elif not body.strip():
                st.error("Ticket description is required.")
            else:
                with st.spinner("Running triage workflow..."):
                    try:
                        result = call_triage_api(
                            subject=subject,
                            body=body,
                            language_hint=language_hint,
                            business_type_hint=business_type_hint,
                            include_draft_response=include_draft_response,
                        )
                        st.session_state.last_submission_result = result
                        st.session_state.auto_refresh_after_submit = True
                        invalidate_read_caches()
                        st.success("Ticket triaged successfully and stored in PostgreSQL.")
                    except Exception as exc:
                        st.error(str(exc))

        if st.session_state.user_role == "admin":
            with st.expander("Simulation Tools", expanded=False):
                st.caption(
                    "Use this only for testing error analytics, retry tracking, and observability behavior."
                )

                if st.button("Run Simulated Error", use_container_width=True):
                    with st.spinner("Creating simulated failure log..."):
                        try:
                            sim_result = call_triage_api(
                                subject="Simulated outage test",
                                body="This is a forced failure used to test error analytics and retry/error views.",
                                language_hint="en",
                                business_type_hint="Demo Scenario",
                                include_draft_response=False,
                                simulate_error=True,
                                allow_error_response=True,
                            )
                            st.session_state.last_simulation_result = sim_result
                            st.session_state.auto_refresh_after_submit = True
                            invalidate_read_caches()
                            st.warning("Simulated error request sent.")
                        except Exception as exc:
                            st.error(str(exc))

                if st.session_state.last_simulation_result:
                    sim_result = st.session_state.last_simulation_result
                    error_response = sim_result.get("error_response") or {}
                    detail = error_response.get("detail") if isinstance(error_response, dict) else None

                    st.markdown(
                        """
                        <div class="simulation-success-card">
                            <strong>Simulated error captured.</strong><br/>
                            This is intentional and is used to validate failure logging, retry count,
                            error analytics, and observability views.
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    if detail:
                        if isinstance(detail, dict):
                            st.caption(f"Error type: {safe_text(detail.get('error_type'))}")
                            st.caption(f"Request ID: {safe_text(detail.get('request_id'))}")
                        else:
                            st.caption(safe_text(detail))

                    render_json_panel(
                        "View simulated error payload",
                        sim_result,
                        expanded=False,
                    )

    with right_col:
        render_feature_card(
            icon="📊",
            title="Business Problem",
            text=(
                "Support teams lose time on manual triage, slow escalation, and inconsistent routing. "
                "This demo shows how AI can reduce repetitive work while keeping decisions structured and auditable."
            ),
            tone="blue",
        )

        render_feature_card(
            icon="✅",
            title="What the Demo Proves",
            text=(
                "A single ticket can be classified, prioritized, enriched, logged, and passed into "
                "downstream automation using one consistent workflow."
            ),
            tone="green",
        )

        render_feature_card(
            icon="⚡",
            title="Best Demo Scenarios",
            text=(
                "Use payment failures, account lockouts, refund requests, or SLA-risk operational "
                "incidents to show escalation logic clearly."
            ),
            tone="purple",
        )

    if st.session_state.last_submission_result:
        st.markdown('<div class="latest-result-shell">', unsafe_allow_html=True)

        result = st.session_state.last_submission_result
        automation = result.get("automation") or {}
        decision = automation.get("decision") or {}
        approval = result.get("approval") or {}

        render_section_header(
            "Latest AI Result",
            "Review the model prediction, escalation decision, approval status, and generated response for the latest ticket.",
        )

        metric_row_1 = st.columns(4)

        with metric_row_1[0]:
            render_metric_card(
                "Queue",
                safe_text(result.get("predicted_queue")),
                "Predicted owner team",
                icon="📁",
                tone="blue",
            )

        with metric_row_1[1]:
            render_metric_card(
                "Priority",
                safe_text(result.get("predicted_priority")).title(),
                "Operational urgency",
                icon="↑",
                tone="orange",
            )

        with metric_row_1[2]:
            render_metric_card(
                "Intent",
                safe_text(result.get("likely_intent")),
                "Likely user need",
                icon="◎",
                tone="purple",
            )

        with metric_row_1[3]:
            conf = result.get("confidence")
            render_metric_card(
                "Confidence",
                f"{conf:.2f}" if isinstance(conf, (int, float)) else safe_text(conf),
                "Model confidence",
                icon="🛡",
                tone="green",
            )

        metric_row_2 = st.columns(4)

        with metric_row_2[0]:
            render_metric_card(
                "SLA Risk",
                bool_text(result.get("sla_risk")),
                "Escalation sensitivity",
                icon="⚠",
                tone="orange",
            )

        with metric_row_2[1]:
            render_metric_card(
                "Latency",
                f"{safe_text(result.get('latency_ms'))} ms",
                "End-to-end response time",
                icon="◷",
                tone="blue",
            )

        with metric_row_2[2]:
            render_metric_card(
                "Retry Count",
                safe_text(result.get("retry_count")),
                "Resilience signal",
                icon="↻",
                tone="cyan",
            )

        with metric_row_2[3]:
            render_metric_card(
                "Escalate",
                bool_text(decision.get("should_escalate")),
                "Automation decision",
                icon="↗",
                tone="red",
            )

        render_badges(
            [
                (f"Target Team: {safe_text(decision.get('target_team'))}", "neutral"),
                (f"Urgency: {safe_text(decision.get('urgency_level'))}", "warning"),
                (
                    f"Approval: {safe_text(approval.get('status'))}",
                    "danger" if approval.get("required") else "success",
                ),
                (f"Request ID: {safe_text(result.get('request_id'))}", "dark"),
            ]
        )

        deterministic_route = result.get("deterministic_route") or {}

        if deterministic_route:
            render_badges(
                [
                    (
                        f"Router: {safe_text(deterministic_route.get('route_family')).title()}",
                        "neutral",
                    ),
                    (
                        f"Specialist: {safe_text(deterministic_route.get('specialist_profile'))}",
                        "dark",
                    ),
                    (
                        f"Router Confidence: {safe_text(deterministic_route.get('confidence_hint')).title()}",
                        "success"
                        if deterministic_route.get("confidence_hint") == "high"
                        else "warning",
                    ),
                ]
            )

            render_json_panel(
                "Deterministic Router Trace",
                deterministic_route,
                expanded=False,
            )

        if approval.get("required"):
            render_result_callout(
                title="Automation is waiting for human approval",
                text=f"Reason: {safe_text(approval.get('reason'))}",
                icon="⏳",
            )

        result_tabs = st.tabs(
            [
                "Summary",
                "Draft Response",
                "Structured Data",
                "Automation",
                "Raw API Response",
            ]
        )

        with result_tabs[0]:
            st.markdown(
                f"""
                <div class="result-summary-box result-summary-blue">
                    {escape(result.get("summary", "No summary available."))}
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                f"""
                <div class="result-summary-box result-summary-green">
                    {escape(result.get("recommended_action", "No recommendation available."))}
                </div>
                """,
                unsafe_allow_html=True,
            )

        with result_tabs[1]:
            st.text_area(
                "Draft Response",
                value=result.get("draft_response", ""),
                height=170,
                key=f"latest_draft_{result.get('request_id', 'latest')}",
            )
            st.caption("Editable for demo use only. Changes here are local and are not saved.")

        with result_tabs[2]:
            render_json_panel(
                "Structured Fields",
                result.get("structured_fields", {}),
                expanded=True,
            )

        with result_tabs[3]:
            render_json_panel(
                "Automation Payload",
                result.get("automation", {}),
                expanded=True,
            )

        with result_tabs[4]:
            render_json_panel(
                "Raw API Response",
                result,
                expanded=False,
            )

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

with tabs[1]:
    st.markdown('<div class="ops-page-shell">', unsafe_allow_html=True)

    if refresh or st.session_state.auto_refresh_after_submit:
        st.session_state.auto_refresh_after_submit = False
        st.rerun()

    logs = load_filtered_logs(
        status=status_filter,
        queue=queue_filter,
        priority=priority_filter,
        search_text=search_filter,
        start_date=start_date,
        end_date=end_date,
        limit=limit_filter,
        offset=offset_filter,
    )

    render_section_header(
        "Operations Dashboard",
        "Monitor processed tickets, queue routing, SLA risk, latency, retries, and recent triage activity.",
    )

    if not logs:
        st.markdown(
            """
            <div class="ops-empty-state-card">
                <div class="info-card-title">No triage logs found</div>
                <div class="info-card-text">
                    Try widening the filters or submit a new ticket to populate the operations dashboard.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    else:
        df = pd.DataFrame(logs)
        metrics = compute_dashboard_metrics(df)

        row1 = st.columns(4)

        with row1[0]:
            render_metric_card(
                "Total Tickets",
                str(metrics["total_logs"]),
                "Filtered records",
                icon="▣",
                tone="blue",
            )

        with row1[1]:
            render_metric_card(
                "Success Rate",
                f"{metrics['success_rate']:.1f}%",
                "Processing reliability",
                icon="✓",
                tone="green",
            )

        with row1[2]:
            render_metric_card(
                "SLA-Risk Rate",
                f"{metrics['sla_risk_rate']:.1f}%",
                "Potential urgency share",
                icon="⚠",
                tone="orange",
            )

        with row1[3]:
            render_metric_card(
                "Escalation Rate",
                f"{metrics['escalation_rate']:.1f}%",
                "Automation-triggered escalation",
                icon="↗",
                tone="purple",
            )

        row2 = st.columns(4)

        with row2[0]:
            render_metric_card(
                "Average Confidence",
                f"{metrics['avg_confidence']:.2f}"
                if metrics["avg_confidence"] is not None
                else "N/A",
                "Model confidence",
                icon="🛡",
                tone="blue",
            )

        with row2[1]:
            render_metric_card(
                "Average Latency",
                f"{metrics['avg_latency_ms']:.2f} ms"
                if metrics["avg_latency_ms"] is not None
                else "N/A",
                "Workflow speed",
                icon="◷",
                tone="purple",
            )

        with row2[2]:
            render_metric_card(
                "Retry Rate",
                f"{metrics['retry_rate']:.1f}%",
                "Resilience indicator",
                icon="↻",
                tone="cyan",
            )

        with row2[3]:
            render_metric_card(
                "Top Queue",
                safe_text(metrics["top_queue"]),
                "Most common owner",
                icon="👥",
                tone="green",
            )

        render_section_header(
            "Distribution View",
            "Understand workload distribution by status, queue, and priority.",
        )

        c1, c2, c3 = st.columns(3, gap="medium")

        with c1:
            with st.container(border=True):
                st.markdown('<div class="ops-card-anchor"></div>', unsafe_allow_html=True)

                render_chart_panel_header(
                    "Status Distribution",
                    "How many tickets were processed successfully versus errors.",
                )

                if "status" in df.columns and df["status"].notna().any():
                    slim_bar_chart(
                        df["status"].fillna("unknown").value_counts(),
                        key="ops_status_chart",
                        height=260,
                    )
                else:
                    st.info("No status data available.")

        with c2:
            with st.container(border=True):
                st.markdown('<div class="ops-card-anchor"></div>', unsafe_allow_html=True)

                render_chart_panel_header(
                    "Queue Distribution",
                    "Which operational queues are receiving the most traffic.",
                )

                if "predicted_queue" in df.columns and df["predicted_queue"].notna().any():
                    slim_bar_chart(
                        df["predicted_queue"].fillna("None").value_counts(),
                        key="ops_queue_chart",
                        height=260,
                    )
                else:
                    st.info("No queue data available.")

        with c3:
            with st.container(border=True):
                st.markdown('<div class="ops-card-anchor"></div>', unsafe_allow_html=True)

                render_chart_panel_header(
                    "Priority Distribution",
                    "How much of the workload is normal versus urgent.",
                )

                if "predicted_priority" in df.columns and df["predicted_priority"].notna().any():
                    slim_bar_chart(
                        df["predicted_priority"].fillna("None").value_counts(),
                        key="ops_priority_chart",
                        height=260,
                    )
                else:
                    st.info("No priority data available.")

        render_section_header(
            "Latency Trend",
            "Track triage response time across recent requests.",
        )

        with st.container(border=True):
            st.markdown('<div class="ops-wide-card-anchor"></div>', unsafe_allow_html=True)

            trend_df = df.copy()
            trend_df["created_at"] = pd.to_datetime(trend_df["created_at"], errors="coerce")
            trend_df["latency_ms"] = pd.to_numeric(trend_df["latency_ms"], errors="coerce")
            trend_df = trend_df.dropna(subset=["created_at", "latency_ms"]).sort_values("created_at")

            if not trend_df.empty:
                full_width_line_chart(
                    trend_df[["created_at", "latency_ms"]],
                    x_col="created_at",
                    y_col="latency_ms",
                    key="ops_latency_trend",
                    height=360,
                )
            else:
                st.info("No latency trend data available for the selected filters.")

        render_section_header(
            "Recent Triage Records",
            "Browse stored triage logs from PostgreSQL using the selected filters and pagination.",
        )

        with st.container(border=True):
            st.markdown('<div class="ops-table-anchor"></div>', unsafe_allow_html=True)

            st.markdown(
                f"""
                <div class="table-action-row">
                    <div class="table-meta-text">
                        Showing page <strong>{int(page_number)}</strong> with up to
                        <strong>{int(page_size)}</strong> records. Offset:
                        <strong>{int(offset_filter)}</strong>.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.download_button(
                label="Export filtered logs to CSV",
                data=to_csv_bytes(df),
                file_name="claudeops_filtered_logs.csv",
                mime="text/csv",
            )

            preferred_columns = [
                "id",
                "request_id",
                "status",
                "provider",
                "model_name",
                "subject",
                "predicted_queue",
                "predicted_priority",
                "likely_intent",
                "sla_risk",
                "confidence",
                "latency_ms",
                "automation_should_escalate",
                "created_at",
            ]

            visible_columns = [col for col in preferred_columns if col in df.columns]
            display_df = humanize_columns(df[visible_columns].copy())

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
            )

            if len(df) == int(page_size):
                st.info(
                    "More records may be available. Increase the page number from the sidebar to view the next page."
                )
            elif int(page_number) > 1 and len(df) == 0:
                st.warning("No records found on this page. Try going back to an earlier page.")

        request_options = df["request_id"].tolist()

        default_request_id = next(
            (
                rid
                for rid in request_options
                if df.loc[df["request_id"] == rid, "status"].iloc[0] == "success"
            ),
            request_options[0],
        )

        default_index = request_options.index(default_request_id)

        st.markdown(
            '<div class="request-selector-label">Select a request to inspect</div>',
            unsafe_allow_html=True,
        )

        selected_request_id = st.selectbox(
            "Select a request to inspect",
            options=request_options,
            index=default_index,
            key="request_selector",
            label_visibility="collapsed",
            format_func=lambda rid: f"{rid} | {df.loc[df['request_id'] == rid, 'subject'].iloc[0][:90]}",
        )

        detail = load_log_detail(selected_request_id)

        if detail:
            render_section_header(
                "Detailed Request Review",
                "Inspect the selected request, AI output, automation payloads, and raw stored JSON.",
            )

            with st.container(border=True):
                st.markdown('<div class="ops-detail-anchor"></div>', unsafe_allow_html=True)

                detail_tabs = st.tabs(["Overview", "Request", "Response", "Automation", "Raw JSON"])

            with detail_tabs[0]:
                detail_row_1 = st.columns(3)

                with detail_row_1[0]:
                    render_metric_card(
                        "Request ID",
                        safe_text(detail["request_id"]),
                        "Stored workflow identifier",
                        icon="▣",
                        tone="blue",
                    )

                with detail_row_1[1]:
                    render_metric_card(
                        "Queue",
                        safe_text(detail["predicted_queue"]),
                        "Predicted owner team",
                        icon="📁",
                        tone="blue",
                    )

                with detail_row_1[2]:
                    render_metric_card(
                        "Latency",
                        f"{safe_text(detail['latency_ms'])} ms",
                        "End-to-end response time",
                        icon="◷",
                        tone="purple",
                    )

                detail_row_2 = st.columns(3)

                with detail_row_2[0]:
                    render_metric_card(
                        "Status",
                        safe_text(detail["status"]).title(),
                        "Workflow result",
                        icon="✓" if detail["status"] == "success" else "!",
                        tone="green" if detail["status"] == "success" else "red",
                    )

                with detail_row_2[1]:
                    render_metric_card(
                        "Priority",
                        safe_text(detail["predicted_priority"]).title(),
                        "Operational urgency",
                        icon="⚑",
                        tone="orange",
                    )

                with detail_row_2[2]:
                    render_metric_card(
                        "Escalate",
                        bool_text(detail["automation_should_escalate"]),
                        "Automation decision",
                        icon="↗",
                        tone="purple",
                    )

                detail_row_3 = st.columns(3)

                with detail_row_3[0]:
                    render_metric_card(
                        "Provider",
                        safe_text(detail["provider"]),
                        "LLM provider",
                        icon="⚙",
                        tone="blue",
                    )

                with detail_row_3[1]:
                    render_metric_card(
                        "Intent",
                        safe_text(detail["likely_intent"]),
                        "Detected customer need",
                        icon="◎",
                        tone="purple",
                    )

                with detail_row_3[2]:
                    render_metric_card(
                        "Target Team",
                        safe_text(detail["automation_target_team"]),
                        "Escalation destination",
                        icon="👥",
                        tone="green",
                    )

                render_badges(
                    [
                        (
                            f"SLA Risk: {bool_text(detail['sla_risk'])}",
                            "danger" if detail["sla_risk"] else "success",
                        ),
                        (
                            f"Human Review: {bool_text(detail['needs_human_review'])}",
                            "warning" if detail["needs_human_review"] else "success",
                        ),
                        (
                            f"Urgency: {safe_text(detail['automation_urgency_level'])}",
                            "neutral",
                        ),
                        (
                            f"Automation Ready: {bool_text(detail['automation_ready'])}",
                            "success" if detail["automation_ready"] else "warning",
                        ),
                    ]
                )

                st.markdown(
                    f"""
                    <div class="detail-message detail-message-blue">
                        {escape(detail["summary"] or "No summary available.")}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.markdown(
                    f"""
                    <div class="detail-message detail-message-green">
                        {escape(detail["recommended_action"] or "No recommendation available.")}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.markdown(
                    f"""
                    <div class="detail-message detail-message-yellow">
                        {escape(detail["urgency_reason"] or "No urgency reason available.")}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with detail_tabs[1]:
                st.code(detail["subject"] or "", language=None)

                st.text_area(
                    "Ticket Body",
                    value=detail["body"] or "",
                    height=220,
                    disabled=True,
                )

                if detail["status"] == "error" and not (detail["structured_fields"] or {}):
                    st.info(
                        "No structured fields are available because this request failed before a valid triage response was produced."
                    )
                else:
                    render_json_panel(
                        "Structured Fields",
                        detail["structured_fields"] or {},
                        expanded=True,
                    )

            with detail_tabs[2]:
                if detail["status"] == "error":
                    st.info(
                        "No draft response is available because this request failed intentionally or before a valid model response was produced."
                    )

                    if detail["error_message"]:
                        st.error(detail["error_message"])
                else:
                    st.text_area(
                        "Draft Response",
                        value=detail["draft_response"] or "",
                        height=170,
                        key=f"detail_draft_{detail['request_id']}",
                    )

                    st.caption("Editable for demo use only. Changes here are local and are not saved.")

            with detail_tabs[3]:
                auto1, auto2, auto3 = st.columns(3)

                with auto1:
                    render_metric_card(
                        "Automation Ready",
                        bool_text(detail["automation_ready"]),
                        "Payloads available",
                        icon="⚡",
                        tone="green" if detail["automation_ready"] else "orange",
                    )

                with auto2:
                    render_metric_card(
                        "Should Escalate",
                        bool_text(detail["automation_should_escalate"]),
                        "Rule-based decision",
                        icon="↗",
                        tone="purple",
                    )

                with auto3:
                    render_metric_card(
                        "Target Team",
                        safe_text(detail["automation_target_team"]),
                        "Escalation destination",
                        icon="👥",
                        tone="blue",
                    )

                if detail["status"] == "error":
                    st.info(
                        "Automation did not run because this request failed before a valid triage response was produced."
                    )

                    if detail["automation_error"]:
                        st.warning(detail["automation_error"])
                else:
                    render_section_header(
                        "Automation Decision",
                        "Rule-based automation decision stored with the selected triage request.",
                    )

                    render_json_panel(
                        "Automation Decision JSON",
                        detail["automation_decision"] or {},
                        expanded=True,
                    )

                    sub1, sub2, sub3, sub4 = st.tabs(
                        ["Slack", "Generic Webhook", "Zapier", "Make"]
                    )

                    with sub1:
                        if detail["automation_slack_delivery"]:
                            render_json_panel(
                                "Slack Delivery Payload",
                                detail["automation_slack_delivery"],
                                expanded=True,
                            )
                        else:
                            st.info("No Slack delivery payload available.")

                    with sub2:
                        if detail["automation_webhook_delivery"]:
                            render_json_panel(
                                "Generic Webhook Payload",
                                detail["automation_webhook_delivery"],
                                expanded=True,
                            )
                        else:
                            st.info("No generic webhook payload available.")

                    with sub3:
                        if detail["automation_zapier_delivery"]:
                            render_json_panel(
                                "Zapier Delivery Payload",
                                detail["automation_zapier_delivery"],
                                expanded=True,
                            )
                        else:
                            st.info("No Zapier payload available.")

                    with sub4:
                        if detail["automation_make_delivery"]:
                            render_json_panel(
                                "Make Delivery Payload",
                                detail["automation_make_delivery"],
                                expanded=True,
                            )
                        else:
                            st.info("No Make payload available.")

            with detail_tabs[4]:
                raw_left, raw_right = st.columns(2)

                with raw_left:
                    render_json_panel(
                        "Raw Request Payload",
                        detail["raw_request"],
                        expanded=True,
                    )

                with raw_right:
                    render_json_panel(
                        "Raw LLM Output",
                        detail["raw_llm_output"],
                        expanded=True,
                    )

    st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.user_role in {"admin", "ops_analyst"}:
    with tabs[2]:
        st.markdown('<div class="approval-page-shell">', unsafe_allow_html=True)

        render_section_header(
            "Approval Queue",
            "Critical automation plans wait here for human approval before external actions are executed.",
        )

        last_policy_decisions = st.session_state.get("last_policy_decisions")
        last_approval_message = st.session_state.get("last_approval_message")

        if last_approval_message:
            st.markdown(
                f"""
                <div class="approval-result-card">
                    <div class="approval-result-title">Latest approval result</div>
                    <div class="approval-result-text">{escape(last_approval_message)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if last_policy_decisions:
            render_json_panel(
                "Latest Policy Engine Decisions",
                last_policy_decisions,
                expanded=True,
            )

            if st.button("Clear Policy Decision View", use_container_width=True):
                st.session_state.pop("last_policy_decisions", None)
                st.session_state.pop("last_approval_message", None)
                st.rerun()

        try:
            pending_items = load_pending_approvals(limit=50)
        except Exception as exc:
            pending_items = []
            st.error(f"Could not load approval queue: {exc}")

        if not pending_items:
            st.markdown(
                """
                <div class="approval-empty-card">
                    <div class="info-card-title">No pending approvals</div>
                    <div class="info-card-text">
                        All critical automation requests have already been reviewed.
                        New approval-required tickets will appear here.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        else:
            for item in pending_items:
                with st.container(border=True):
                    render_approval_ticket_summary(item)
        
                    action_col1, action_col2 = st.columns(2)
        
                    with action_col1:
                        if st.button(
                            "✓ Approve & Execute Automation",
                            key=f"approve_{item['request_id']}",
                            use_container_width=True,
                            type="primary",
                        ):
                            try:
                                response = approve_pending_request_api(
                                    request_id=item["request_id"],
                                    actor=st.session_state.username,
                                    actor_role=st.session_state.user_role,
                                )
        
                                st.session_state.last_approval_message = response.get(
                                    "message",
                                    "Approval completed.",
                                )
                                st.session_state.last_policy_decisions = response.get(
                                    "policy_decisions"
                                )
        
                                invalidate_read_caches()
                                st.rerun()
        
                            except Exception as exc:
                                st.error(str(exc))
        
                    with action_col2:
                        if st.button(
                            "⊘ Reject Automation",
                            key=f"reject_{item['request_id']}",
                            use_container_width=True,
                            type="secondary",
                        ):
                            try:
                                response = reject_pending_request_api(
                                    request_id=item["request_id"],
                                    actor=st.session_state.username,
                                    actor_role=st.session_state.user_role,
                                )
        
                                st.session_state.last_approval_message = response.get(
                                    "message",
                                    "Approval rejected.",
                                )
                                st.session_state.last_policy_decisions = None
        
                                invalidate_read_caches()
                                st.rerun()
        
                            except Exception as exc:
                                st.error(str(exc))

if st.session_state.user_role == "admin":
    with tabs[3]:
        st.markdown('<div class="integration-page-shell">', unsafe_allow_html=True)

        render_section_header(
            "Integrations & Benchmark",
            "Review Zapier/Make readiness, outbound workflow contracts, benchmark runs, benchmark charts, and benchmark history.",
        )

        try:
            api_config = load_api_config()
        except Exception as exc:
            api_config = {}
            st.error(f"Could not load API config: {exc}")

        integration_html = '<div class="integration-status-grid">'

        integration_html += render_integration_status_card_v2(
            "Zapier Hook",
            "Enabled" if api_config.get("zapier_hook_enabled") else "Off",
            "Feature switch for Zapier workflow delivery",
            "✓" if api_config.get("zapier_hook_enabled") else "!",
            "green" if api_config.get("zapier_hook_enabled") else "orange",
        )

        integration_html += render_integration_status_card_v2(
            "Zapier URL",
            "Configured" if api_config.get("zapier_webhook_configured") else "Missing",
            "Webhook endpoint availability",
            "↗" if api_config.get("zapier_webhook_configured") else "!",
            "blue" if api_config.get("zapier_webhook_configured") else "red",
        )

        integration_html += render_integration_status_card_v2(
            "Make Hook",
            "Enabled" if api_config.get("make_hook_enabled") else "Off",
            "Feature switch for Make scenario delivery",
            "✓" if api_config.get("make_hook_enabled") else "!",
            "green" if api_config.get("make_hook_enabled") else "orange",
        )

        integration_html += render_integration_status_card_v2(
            "Make URL",
            "Configured" if api_config.get("make_webhook_configured") else "Missing",
            "Webhook endpoint availability",
            "↗" if api_config.get("make_webhook_configured") else "!",
            "blue" if api_config.get("make_webhook_configured") else "red",
        )

        integration_html += "</div>"

        render_html(integration_html)

        render_section_header(
            "Cross-Platform Workflow Contract",
            "A stable outbound automation schema makes Zapier, Make, Slack, and webhook integrations easier to maintain.",
        )

        try:
            contract_spec = load_outbound_contract_spec()
        except Exception as exc:
            contract_spec = {}
            st.error(f"Could not load outbound automation contract: {exc}")

        if contract_spec:
            st.markdown(
                """
                <div class="contract-intro-card">
                    <div class="contract-intro-title">Published automation contract</div>
                    <div class="contract-intro-text">
                        This contract keeps outbound actions predictable across workflow platforms.
                        It exposes ticket, triage result, automation decision, downstream actions,
                        and policy flags in a reusable JSON structure.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            contract_html = '<div class="contract-metric-grid">'

            contract_html += render_contract_metric_card(
                "Contract Version",
                safe_text(contract_spec.get("contract_version")),
                "Stable outbound schema",
                "v1",
                "blue",
            )

            contract_html += render_contract_metric_card(
                "Schema Name",
                safe_text(contract_spec.get("schema_name")),
                "Integration contract",
                "▣",
                "purple",
            )

            contract_html += render_contract_metric_card(
                "Integration Style",
                "Cross-platform",
                "Zapier / Make / Slack",
                "↗",
                "orange",
            )

            contract_html += "</div>"

            render_html(contract_html)

            render_json_panel(
                "Recommended Zapier/Make Field Mapping",
                contract_spec.get("recommended_mapping", {}),
                expanded=True,
            )

            render_json_panel(
                "Sample Automation Contract",
                contract_spec.get("sample_contract", {}),
                expanded=False,
            )
        else:
            render_empty_state(
                "No workflow contract available",
                "The contract endpoint did not return data. Check the FastAPI contract route.",
            )

        render_section_header(
            "Benchmark Runner",
            "Run a small benchmark sample to validate routing consistency, latency, escalation logic, and automation readiness.",
        )

        st.markdown(
            """
            <div class="benchmark-runner-card">
                <div class="benchmark-runner-title">Benchmark configuration</div>
                <div class="benchmark-runner-text">
                    Keep the sample size small for portfolio demos. This validates the workflow without creating unnecessary LLM cost.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        bench_col1, bench_col2, bench_col3 = st.columns([1.1, 1.1, 0.9], gap="large")

        with bench_col1:
            benchmark_sample_size = st.slider(
                "Sample Size",
                min_value=1,
                max_value=20,
                value=5,
                step=1,
            )

        with bench_col2:
            benchmark_seed = st.number_input(
                "Random Seed",
                min_value=0,
                max_value=999999,
                value=42,
                step=1,
            )

        with bench_col3:
            st.write("")
            st.write("")
            run_benchmark_button = st.button(
                "Run Benchmark",
                use_container_width=True,
                type="primary",
            )

        if run_benchmark_button:
            with st.spinner("Running benchmark..."):
                try:
                    benchmark_result = run_benchmark_api(
                        sample_size=benchmark_sample_size,
                        random_seed=int(benchmark_seed),
                        include_rows=True,
                    )

                    st.session_state.last_benchmark_result = benchmark_result
                    invalidate_read_caches()

                    st.markdown(
                        """
                        <div class="benchmark-success-strip">
                            ✓ Benchmark completed.
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                except Exception as exc:
                    st.error(str(exc))

        if st.session_state.last_benchmark_result:
            benchmark_result = st.session_state.last_benchmark_result

            if not run_benchmark_button:
                st.markdown(
                    """
                    <div class="benchmark-success-strip">
                        ✓ Latest benchmark result is loaded.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            render_section_header(
                "Benchmark Summary",
                "High-level benchmark results for the latest run.",
            )

            bench_metrics_row = st.columns(5)

            with bench_metrics_row[0]:
                render_metric_card(
                    "Sample Used",
                    str(benchmark_result.get("sample_size_used", 0)),
                    "Tickets tested",
                    icon="▣",
                    tone="blue",
                )

            with bench_metrics_row[1]:
                render_metric_card(
                    "Queue Consistency",
                    f"{benchmark_result.get('queue_prediction_consistency_pct', 0):.2f}%",
                    "Normalized match",
                    icon="✓",
                    tone="green",
                )

            with bench_metrics_row[2]:
                render_metric_card(
                    "Avg Latency",
                    f"{benchmark_result.get('average_latency_ms', 'N/A')} ms",
                    "Benchmark average",
                    icon="◷",
                    tone="purple",
                )

            with bench_metrics_row[3]:
                render_metric_card(
                    "Escalated Tickets",
                    str(benchmark_result.get("escalated_count", 0)),
                    "Rule-based escalation count",
                    icon="↗",
                    tone="orange",
                )

            with bench_metrics_row[4]:
                render_metric_card(
                    "Automation-Ready",
                    str(benchmark_result.get("successful_automation_ready_outputs", 0)),
                    "Successful outputs",
                    icon="⚡",
                    tone="green",
                )

            rows = benchmark_result.get("rows") or []

            if rows:
                benchmark_df = pd.DataFrame(rows)

                render_section_header(
                    "Benchmark Charts",
                    "Visual checks for consistency, priority spread, escalation behavior, and latency distribution.",
                )

                st.markdown('<div class="benchmark-chart-shell">', unsafe_allow_html=True)

                chart_col1, chart_col2 = st.columns(2)

                with chart_col1:
                    with st.container(border=True):
                        render_chart_panel_header(
                            "Queue Consistency",
                            "Match versus mismatch across benchmark samples.",
                        )

                        if "queue_match" in benchmark_df.columns:
                            slim_bar_chart(
                                benchmark_df["queue_match"].map(
                                    {True: "Match", False: "Mismatch"}
                                ).value_counts(),
                                key="bench_match_chart",
                                height=250,
                            )
                        else:
                            st.info("No queue consistency data available.")

                with chart_col2:
                    with st.container(border=True):
                        render_chart_panel_header(
                            "Priority Distribution",
                            "Priority levels predicted during the benchmark run.",
                        )

                        if "priority" in benchmark_df.columns and benchmark_df["priority"].notna().any():
                            slim_bar_chart(
                                benchmark_df["priority"].value_counts(),
                                key="bench_priority_chart",
                                height=250,
                            )
                        else:
                            st.info("No priority data available.")

                chart_col3, chart_col4 = st.columns(2)

                with chart_col3:
                    with st.container(border=True):
                        render_chart_panel_header(
                            "Escalation Count",
                            "Escalated versus non-escalated benchmark samples.",
                        )

                        if "escalated" in benchmark_df.columns:
                            slim_bar_chart(
                                benchmark_df["escalated"].map(
                                    {True: "Escalated", False: "Not Escalated"}
                                ).value_counts(),
                                key="bench_escalated_chart",
                                height=250,
                            )
                        else:
                            st.info("No escalation data available.")

                with chart_col4:
                    with st.container(border=True):
                        render_chart_panel_header(
                            "Latency Distribution",
                            "Approximate latency buckets for benchmark responses.",
                        )

                        if "latency_ms" in benchmark_df.columns:
                            hist_series = build_histogram_series(benchmark_df["latency_ms"])

                            if not hist_series.empty:
                                slim_bar_chart(
                                    hist_series,
                                    key="bench_latency_hist",
                                    height=250,
                                )
                            else:
                                st.info("No latency distribution available.")
                        else:
                            st.info("No latency field available.")

                st.markdown("</div>", unsafe_allow_html=True)

                render_section_header(
                    "Sample Row-Level Results",
                    "Detailed benchmark rows for debugging queue matching, escalation, and latency behavior.",
                )

                st.markdown(
                    """
                    <div class="benchmark-table-note">
                        These rows are useful for portfolio screenshots because they prove that the benchmark is not just a static KPI section.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.dataframe(
                    benchmark_df,
                    use_container_width=True,
                    hide_index=True,
                )

                st.download_button(
                    label="Export benchmark rows to CSV",
                    data=to_csv_bytes(benchmark_df),
                    file_name="claudeops_benchmark_results.csv",
                    mime="text/csv",
                )
            else:
                render_empty_state(
                    "No benchmark rows returned",
                    "The benchmark summary completed, but no row-level data was returned.",
                )

        render_section_header(
            "Benchmark History",
            "Stored benchmark runs from PostgreSQL for comparison over time.",
        )

        try:
            history = load_benchmark_history(limit=20)
        except Exception as exc:
            history = []
            st.error(f"Could not load benchmark history: {exc}")

        if history:
            history_df = pd.DataFrame(history)

            preferred_history_columns = [
                "id",
                "provider",
                "model_name",
                "sample_size",
                "queue_prediction_consistency_pct",
                "average_latency_ms",
                "escalated_count",
                "successful_automation_ready_outputs",
                "created_at",
            ]

            visible_history_columns = [
                col for col in preferred_history_columns if col in history_df.columns
            ]

            st.dataframe(
                history_df[visible_history_columns].copy(),
                use_container_width=True,
                hide_index=True,
            )

            history_chart_df = history_df.copy()
            history_chart_df["created_at"] = pd.to_datetime(
                history_chart_df["created_at"],
                errors="coerce",
            )
            history_chart_df = history_chart_df.dropna(subset=["created_at"]).sort_values("created_at")

            if not history_chart_df.empty:
                trend_col1, trend_col2 = st.columns(2)

                with trend_col1:
                    with st.container(border=True):
                        render_chart_panel_header(
                            "Queue Consistency Over Time",
                            "Benchmark consistency trend across recent runs.",
                        )

                        if "queue_prediction_consistency_pct" in history_chart_df.columns:
                            history_queue_trend = history_chart_df[
                                ["created_at", "queue_prediction_consistency_pct"]
                            ].dropna()

                            full_width_line_chart(
                                history_queue_trend,
                                x_col="created_at",
                                y_col="queue_prediction_consistency_pct",
                                key="benchmark_history_queue_consistency",
                                height=260,
                            )
                        else:
                            st.info("No queue consistency trend data available.")

                with trend_col2:
                    with st.container(border=True):
                        render_chart_panel_header(
                            "Average Latency Over Time",
                            "Benchmark latency trend across recent runs.",
                        )

                        if "average_latency_ms" in history_chart_df.columns:
                            history_latency_trend = history_chart_df[
                                ["created_at", "average_latency_ms"]
                            ].dropna()

                            full_width_line_chart(
                                history_latency_trend,
                                x_col="created_at",
                                y_col="average_latency_ms",
                                key="benchmark_history_average_latency",
                                height=260,
                            )
                        else:
                            st.info("No latency trend data available.")
        else:
            render_empty_state(
                "No benchmark history available",
                "Run a benchmark to populate history, trend charts, and comparison rows.",
            )

        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[4]:
        st.markdown('<div class="observability-page-shell">', unsafe_allow_html=True)

        render_section_header(
            "Observability & Evaluation",
            "Monitor latency, errors, confidence drift, token usage, cost, correction feedback, policy audit, and benchmark quality.",
        )

        monitoring_windows = {
            "Last 1 hour": 1,
            "Last 6 hours": 6,
            "Last 24 hours": 24,
            "Last 3 days": 72,
            "Last 1 week": 168,
            "Last 30 days": 720,
        }

        obs_intro_left, obs_intro_right = st.columns([0.9, 2.1], gap="large")

        with obs_intro_left:
            st.markdown(
                """
                <div class="obs-window-card">
                    <div class="obs-window-title">Monitoring window</div>
                    <div class="obs-window-text">
                        Select the time range used by the backend observability summary API.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            selected_window_label = st.selectbox(
                "Monitoring Window",
                options=list(monitoring_windows.keys()),
                index=2,
            )

            obs_hours = monitoring_windows[selected_window_label]

        with obs_intro_right:
            render_obs_intro_panel(selected_window_label)

        try:
            obs = load_observability_summary(hours=int(obs_hours))
        except Exception as exc:
            obs = {}
            st.error(f"Could not load observability summary: {exc}")

        if obs:
            with st.container(border=True):
                render_obs_section_header_v2(
                    "01",
                    "Runtime Health",
                    "Track successful runs, failures, average latency, and worst-case response time.",
                    selected_window_label,
                )

                health_row = st.columns(4)

                with health_row[0]:
                    render_metric_card(
                        "Total Runs",
                        str(obs.get("total_runs", 0)),
                        "Workflow executions",
                        icon="▣",
                        tone="blue",
                    )

                with health_row[1]:
                    error_rate = obs.get("error_rate_pct", 0)
                    render_metric_card(
                        "Error Rate",
                        f"{error_rate:.2f}%" if isinstance(error_rate, (int, float)) else "0.00%",
                        f"{obs.get('error_count', 0)} errors",
                        icon="!",
                        tone="red" if error_rate else "green",
                    )

                with health_row[2]:
                    avg_latency = obs.get("average_latency_ms")
                    render_metric_card(
                        "Avg Latency",
                        f"{avg_latency:.2f} ms" if isinstance(avg_latency, (int, float)) else "N/A",
                        "LLM workflow speed",
                        icon="◷",
                        tone="purple",
                    )

                with health_row[3]:
                    max_latency = obs.get("max_latency_ms")
                    render_metric_card(
                        "Max Latency",
                        f"{max_latency:.2f} ms" if isinstance(max_latency, (int, float)) else "N/A",
                        "Worst recent run",
                        icon="↗",
                        tone="orange",
                    )

            with st.container(border=True):
                render_obs_section_header_v2(
                    "02",
                    "Token & Cost Monitoring",
                    "Track input tokens, output tokens, total usage, and estimated LLM cost.",
                    selected_window_label,
                )

                token_row = st.columns(4)

                with token_row[0]:
                    render_metric_card(
                        "Input Tokens",
                        str(obs.get("total_input_tokens", 0)),
                        "Prompt/context tokens",
                        icon="→",
                        tone="blue",
                    )

                with token_row[1]:
                    render_metric_card(
                        "Output Tokens",
                        str(obs.get("total_output_tokens", 0)),
                        "Model response tokens",
                        icon="←",
                        tone="purple",
                    )

                with token_row[2]:
                    render_metric_card(
                        "Total Tokens",
                        str(obs.get("total_tokens", 0)),
                        "Input + output",
                        icon="Σ",
                        tone="orange",
                    )

                with token_row[3]:
                    cost_value = obs.get("estimated_cost_usd", 0)
                    render_metric_card(
                        "Estimated Cost",
                        f"${cost_value:.6f}" if isinstance(cost_value, (int, float)) else "$0.000000",
                        "Based on env token rates",
                        icon="$",
                        tone="green",
                    )

                if obs.get("estimated_cost_usd", 0) == 0:
                    st.info(
                        "Cost is showing as zero because LLM_INPUT_COST_PER_1M_TOKENS and "
                        "LLM_OUTPUT_COST_PER_1M_TOKENS are currently set to 0.0."
                    )

            with st.container(border=True):
                render_obs_section_header_v2(
                    "03",
                    "Drift / Alert Monitor",
                    "Surface latency spikes, error spikes, and low-confidence spikes from recent trace data.",
                    selected_window_label,
                )

                alerts = obs.get("alerts") or []

                if alerts:
                    for alert in alerts:
                        render_observability_alert(
                            alert_type=safe_text(alert.get("type"), "unknown"),
                            message=safe_text(alert.get("message"), "Alert triggered."),
                            severity=safe_text(alert.get("severity"), "medium"),
                        )
                else:
                    st.markdown(
                        """
                        <div class="obs-alert-success-box">
                            ✓ No latency, error, or low-confidence drift alerts in this window.
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                drift_row = st.columns(3)

                with drift_row[0]:
                    render_metric_card(
                        "Low Confidence Rate",
                        f"{obs.get('low_confidence_rate_pct', 0):.2f}%",
                        f"{obs.get('low_confidence_count', 0)} low-confidence runs",
                        icon="?",
                        tone="orange",
                    )

                with drift_row[1]:
                    render_metric_card(
                        "Feedback Count",
                        str(obs.get("feedback_count", 0)),
                        "Human corrections submitted",
                        icon="✎",
                        tone="blue",
                    )

                with drift_row[2]:
                    render_metric_card(
                        "Queue Feedback Accuracy",
                        f"{obs.get('queue_feedback_accuracy_pct', 0):.2f}%",
                        "Based on human feedback",
                        icon="✓",
                        tone="green",
                    )

            with st.container(border=True):
                render_obs_section_header_v2(
                    "04",
                    "Correction-Aware Benchmark Analytics",
                    "Compare raw model accuracy against human-corrected labels and review weak routing areas.",
                    "Feedback benchmark",
                )

                benchmark_windows = {
                    "Last 7 days": 7,
                    "Last 30 days": 30,
                    "Last 90 days": 90,
                    "Last 365 days": 365,
                }

                selected_benchmark_window = st.selectbox(
                    "Benchmark Accuracy Window",
                    options=list(benchmark_windows.keys()),
                    index=1,
                    key="correction_aware_benchmark_window",
                )

                benchmark_days = benchmark_windows[selected_benchmark_window]

                try:
                    accuracy_summary = load_correction_aware_benchmark_summary(
                        days=int(benchmark_days)
                    )
                except Exception as exc:
                    accuracy_summary = {}
                    st.error(f"Could not load correction-aware benchmark summary: {exc}")

                if accuracy_summary:
                    raw_summary = accuracy_summary.get("raw_accuracy_summary") or {}
                    corrected_summary = accuracy_summary.get("correction_aware_accuracy_summary") or {}

                    accuracy_cols = st.columns(4)

                    with accuracy_cols[0]:
                        render_metric_card(
                            "Raw Queue Accuracy",
                            f"{raw_summary.get('queue_accuracy_pct', 0):.2f}%",
                            "Before correction loop",
                            icon="◎",
                            tone="orange",
                        )

                    with accuracy_cols[1]:
                        render_metric_card(
                            "Corrected Queue Accuracy",
                            f"{corrected_summary.get('queue_accuracy_pct', 0):.2f}%",
                            "After human correction",
                            icon="✓",
                            tone="green",
                        )

                    with accuracy_cols[2]:
                        render_metric_card(
                            "Feedback Samples",
                            str(accuracy_summary.get("feedback_count", 0)),
                            "Reviewed records",
                            icon="✎",
                            tone="blue",
                        )

                    with accuracy_cols[3]:
                        render_metric_card(
                            "Benchmark Window",
                            selected_benchmark_window,
                            "Stored logs only",
                            icon="◷",
                            tone="purple",
                        )

                    field_accuracy = accuracy_summary.get("field_accuracy") or []
                    if field_accuracy:
                        st.markdown("#### Field-Level Accuracy")
                        st.dataframe(
                            pd.DataFrame(field_accuracy),
                            use_container_width=True,
                            hide_index=True,
                        )

                    accuracy_by_queue = accuracy_summary.get("accuracy_by_predicted_queue") or []
                    if accuracy_by_queue:
                        st.markdown("#### Accuracy by Predicted Queue")
                        st.dataframe(
                            pd.DataFrame(accuracy_by_queue),
                            use_container_width=True,
                            hide_index=True,
                        )
                    else:
                        st.info("No queue-level feedback data available yet.")

                    router_family_accuracy = accuracy_summary.get("router_family_accuracy") or []
                    if router_family_accuracy:
                        st.markdown("#### Router Specialist Performance")
                        st.dataframe(
                            pd.DataFrame(router_family_accuracy),
                            use_container_width=True,
                            hide_index=True,
                        )
                    else:
                        st.info("No router-family feedback data available yet.")

                    confusion_matrix = accuracy_summary.get("queue_confusion_matrix") or []
                    if confusion_matrix:
                        st.markdown("#### Predicted Queue vs Final Corrected Queue")
                        st.dataframe(
                            pd.DataFrame(confusion_matrix),
                            use_container_width=True,
                            hide_index=True,
                        )
                    else:
                        st.info("No queue confusion data available yet.")

                    worst_queues = accuracy_summary.get("worst_performing_queues") or []
                    if worst_queues:
                        st.markdown("#### Worst-Performing Queues")
                        st.dataframe(
                            pd.DataFrame(worst_queues),
                            use_container_width=True,
                            hide_index=True,
                        )

                    recent_corrections = accuracy_summary.get("recent_corrections") or []
                    if recent_corrections:
                        render_json_panel(
                            "Recent Human Corrections",
                            recent_corrections,
                            expanded=False,
                        )

                    with st.expander("Benchmark Notes", expanded=False):
                        for note in accuracy_summary.get("notes", []):
                            st.write(f"- {note}")
                else:
                    render_empty_state(
                        "No correction-aware benchmark data",
                        "Save human feedback corrections to populate this benchmark section.",
                    )

            with st.container(border=True):
                render_obs_section_header_v2(
                    "05",
                    "Benchmark History Comparison",
                    "Compare benchmark accuracy and latency across recent benchmark runs.",
                    "Historical runs",
                )

                benchmark_history = obs.get("recent_benchmark_history") or []

                if benchmark_history:
                    bench_history_df = pd.DataFrame(benchmark_history)

                    st.markdown(
                        """
                        <div class="obs-table-note">
                            Recent benchmark history proves the workflow is tracked over time, not only evaluated once.
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    st.dataframe(
                        bench_history_df,
                        use_container_width=True,
                        hide_index=True,
                    )

                    bench_history_df["created_at"] = pd.to_datetime(
                        bench_history_df["created_at"],
                        errors="coerce",
                    )
                    bench_history_df = bench_history_df.dropna(subset=["created_at"]).sort_values("created_at")

                    if not bench_history_df.empty:
                        chart_col1, chart_col2 = st.columns(2)

                        with chart_col1:
                            with st.container(border=True):
                                render_chart_panel_header(
                                    "Queue Consistency Trend",
                                    "Queue consistency percentage across benchmark runs.",
                                )

                                if "queue_prediction_consistency_pct" in bench_history_df.columns:
                                    obs_queue_trend = bench_history_df[
                                        ["created_at", "queue_prediction_consistency_pct"]
                                    ].dropna()

                                    full_width_line_chart(
                                        obs_queue_trend,
                                        x_col="created_at",
                                        y_col="queue_prediction_consistency_pct",
                                        key="obs_benchmark_queue_consistency",
                                        height=260,
                                    )
                                else:
                                    st.info("No queue consistency trend data available.")

                        with chart_col2:
                            with st.container(border=True):
                                render_chart_panel_header(
                                    "Average Latency Trend",
                                    "Average benchmark latency across recent runs.",
                                )

                                if "average_latency_ms" in bench_history_df.columns:
                                    obs_latency_trend = bench_history_df[
                                        ["created_at", "average_latency_ms"]
                                    ].dropna()

                                    full_width_line_chart(
                                        obs_latency_trend,
                                        x_col="created_at",
                                        y_col="average_latency_ms",
                                        key="obs_benchmark_average_latency",
                                        height=260,
                                    )
                                else:
                                    st.info("No latency trend data available.")
                else:
                    st.info("No benchmark history available yet. Run a benchmark to populate this section.")

            with st.container(border=True):
                render_obs_section_header_v2(
                    "06",
                    "Human Feedback Correction Loop",
                    "Correct queue, priority, intent, and recommended action. Corrections are saved back to PostgreSQL.",
                    "Human review",
                )

                recent_feedback_logs = load_filtered_logs(
                    status="success",
                    queue="All",
                    priority="All",
                    search_text="",
                    start_date=None,
                    end_date=None,
                    limit=50,
                    offset=0,
                )

                if not recent_feedback_logs:
                    st.info("No successful logs available for feedback yet.")
                else:
                    feedback_df = pd.DataFrame(recent_feedback_logs)
                    request_options = feedback_df["request_id"].tolist()

                    selected_feedback_request_id = st.selectbox(
                        "Select request for correction",
                        options=request_options,
                        format_func=lambda rid: f"{rid} | {feedback_df.loc[feedback_df['request_id'] == rid, 'subject'].iloc[0][:80]}",
                    )

                    selected_feedback_row = feedback_df[
                        feedback_df["request_id"] == selected_feedback_request_id
                    ].iloc[0]

                    raw_queue = safe_text(selected_feedback_row.get("predicted_queue"))
                    raw_priority = safe_text(selected_feedback_row.get("predicted_priority"))
                    raw_intent = safe_text(selected_feedback_row.get("likely_intent"))
                    raw_action = safe_text(selected_feedback_row.get("recommended_action"))

                    st.markdown(
                        """
                        <div class="obs-feedback-card">
                            <div class="obs-feedback-title">Raw AI Prediction</div>
                            <div class="obs-feedback-text">
                                Review the current model output before saving human correction feedback.
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    raw_cols = st.columns(4)

                    with raw_cols[0]:
                        render_metric_card(
                            "Raw Queue",
                            raw_queue,
                            "AI prediction",
                            icon="📁",
                            tone="blue",
                            compact=True,
                        )

                    with raw_cols[1]:
                        render_metric_card(
                            "Raw Priority",
                            raw_priority,
                            "AI prediction",
                            icon="⚑",
                            tone="orange",
                            compact=True,
                        )

                    with raw_cols[2]:
                        render_metric_card(
                            "Raw Intent",
                            raw_intent,
                            "AI prediction",
                            icon="◎",
                            tone="purple",
                            compact=True,
                        )

                    with raw_cols[3]:
                        render_metric_card(
                            "Confidence",
                            safe_text(selected_feedback_row.get("confidence")),
                            "AI confidence",
                            icon="🛡",
                            tone="green",
                            compact=True,
                        )

                    st.text_area(
                        "Raw Recommended Action",
                        value=raw_action,
                        height=90,
                        disabled=True,
                    )

                    queue_options = filter_options.get("queues", [])
                    priority_options = filter_options.get("priorities", [])

                    with st.form("triage_correction_form"):
                        st.markdown("#### Human Correction")

                        corr_col1, corr_col2 = st.columns(2)

                        with corr_col1:
                            queue_correct = st.radio(
                                "Was the queue correct?",
                                options=[True, False],
                                index=0,
                                format_func=lambda value: "Yes" if value else "No",
                                horizontal=True,
                            )

                            corrected_queue = st.selectbox(
                                "Correct queue, only if queue was wrong",
                                options=[""] + queue_options,
                                index=0,
                            )

                            priority_correct = st.radio(
                                "Was the priority correct?",
                                options=[True, False],
                                index=0,
                                format_func=lambda value: "Yes" if value else "No",
                                horizontal=True,
                            )

                            corrected_priority = st.selectbox(
                                "Correct priority, only if priority was wrong",
                                options=[""] + priority_options,
                                index=0,
                            )

                        with corr_col2:
                            intent_correct = st.radio(
                                "Was the intent correct?",
                                options=[True, False],
                                index=0,
                                format_func=lambda value: "Yes" if value else "No",
                                horizontal=True,
                            )

                            corrected_intent = st.text_input(
                                "Correct intent, only if intent was wrong",
                                value="",
                                placeholder="Example: payment_issue",
                            )

                            recommended_action_correct = st.radio(
                                "Was the recommended action correct?",
                                options=[True, False],
                                index=0,
                                format_func=lambda value: "Yes" if value else "No",
                                horizontal=True,
                            )

                        corrected_recommended_action = st.text_area(
                            "Correct recommended action, only if action was wrong",
                            value="",
                            height=110,
                            placeholder="Example: Escalate to payment operations team and investigate gateway errors.",
                        )

                        feedback_notes = st.text_area(
                            "Feedback notes",
                            value="",
                            height=100,
                            placeholder="Example: Payment failures should route to Billing and Payments with high priority.",
                        )

                        feedback_submit = st.form_submit_button(
                            "Save Correction Feedback",
                            use_container_width=True,
                        )

                    if feedback_submit:
                        try:
                            saved_feedback = submit_triage_feedback_api(
                                request_id=selected_feedback_request_id,
                                queue_correct=queue_correct,
                                corrected_queue=corrected_queue,
                                priority_correct=priority_correct,
                                corrected_priority=corrected_priority,
                                intent_correct=intent_correct,
                                corrected_intent=corrected_intent,
                                recommended_action_correct=recommended_action_correct,
                                corrected_recommended_action=corrected_recommended_action,
                                corrected_by=st.session_state.username,
                                correction_source="streamlit_observability",
                                notes=feedback_notes,
                            )

                            invalidate_read_caches()
                            st.success("Correction feedback saved successfully.")

                            render_json_panel(
                                "Saved Correction Feedback",
                                saved_feedback,
                                expanded=False,
                            )

                        except Exception as exc:
                            st.error(f"Could not save correction feedback: {exc}")

            with st.container(border=True):
                render_obs_section_header_v2(
                    "07",
                    "Correction Analytics",
                    "Summarize human correction volume and compare raw benchmark accuracy with correction-aware accuracy.",
                    "Evaluation loop",
                )

                correction_summary = obs.get("feedback_correction_summary") or {}
                raw_benchmark = obs.get("benchmark_without_corrections") or {}
                corrected_benchmark = obs.get("benchmark_with_corrections") or {}
                correction_rate_by_queue = obs.get("correction_rate_by_queue") or []

                correction_cols = st.columns(4)

                with correction_cols[0]:
                    render_metric_card(
                        "Feedback Count",
                        str(correction_summary.get("feedback_count", 0)),
                        "Reviewed predictions",
                        icon="✎",
                        tone="blue",
                    )

                with correction_cols[1]:
                    render_metric_card(
                        "Queue Corrections",
                        str(correction_summary.get("queue_correction_count", 0)),
                        "Queue fixes submitted",
                        icon="📁",
                        tone="orange",
                    )

                with correction_cols[2]:
                    render_metric_card(
                        "Priority Corrections",
                        str(correction_summary.get("priority_correction_count", 0)),
                        "Priority fixes submitted",
                        icon="⚑",
                        tone="purple",
                    )

                with correction_cols[3]:
                    render_metric_card(
                        "Intent Corrections",
                        str(correction_summary.get("intent_correction_count", 0)),
                        "Intent fixes submitted",
                        icon="◎",
                        tone="green",
                    )

                st.markdown("#### Benchmark: Raw vs Correction-Aware")

                benchmark_compare_df = pd.DataFrame(
                    [
                        {
                            "metric": "Queue Accuracy",
                            "raw_prediction_pct": raw_benchmark.get("queue_accuracy_pct", 0),
                            "after_correction_pct": corrected_benchmark.get("queue_accuracy_pct", 0),
                        },
                        {
                            "metric": "Priority Accuracy",
                            "raw_prediction_pct": raw_benchmark.get("priority_accuracy_pct", 0),
                            "after_correction_pct": corrected_benchmark.get("priority_accuracy_pct", 0),
                        },
                        {
                            "metric": "Intent Accuracy",
                            "raw_prediction_pct": raw_benchmark.get("intent_accuracy_pct", 0),
                            "after_correction_pct": corrected_benchmark.get("intent_accuracy_pct", 0),
                        },
                        {
                            "metric": "Recommended Action Accuracy",
                            "raw_prediction_pct": raw_benchmark.get("recommended_action_accuracy_pct", 0),
                            "after_correction_pct": corrected_benchmark.get("recommended_action_accuracy_pct", 0),
                        },
                    ]
                )

                st.dataframe(
                    benchmark_compare_df,
                    use_container_width=True,
                    hide_index=True,
                )

                if correction_rate_by_queue:
                    st.markdown("#### Correction Rate by Predicted Queue")
                    st.dataframe(
                        pd.DataFrame(correction_rate_by_queue),
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info("No correction-rate-by-queue data yet. Save feedback to populate this section.")

            with st.container(border=True):
                render_obs_section_header_v2(
                    "08",
                    "Policy-Based Tool Access Audit",
                    "Review allowed and blocked outbound actions for governance, least privilege, and automation control.",
                    "Governance",
                )

                try:
                    policy_audit_items = load_policy_audit(limit=50)
                except Exception as exc:
                    policy_audit_items = []
                    st.error(f"Could not load policy audit: {exc}")

                if policy_audit_items:
                    policy_df = pd.DataFrame(policy_audit_items)

                    policy_metrics = st.columns(3)

                    with policy_metrics[0]:
                        allowed_count = int((policy_df["decision"] == "allowed").sum())
                        render_metric_card(
                            "Allowed Actions",
                            str(allowed_count),
                            "Passed policy checks",
                            icon="✓",
                            tone="green",
                        )

                    with policy_metrics[1]:
                        blocked_count = int((policy_df["decision"] == "blocked").sum())
                        render_metric_card(
                            "Blocked Actions",
                            str(blocked_count),
                            "Stopped by governance rules",
                            icon="!",
                            tone="red",
                        )

                    with policy_metrics[2]:
                        admin_actions = int((policy_df["actor_role"] == "admin").sum())
                        render_metric_card(
                            "Admin Actions",
                            str(admin_actions),
                            "Actions requested by admin",
                            icon="🛡",
                            tone="blue",
                        )

                    st.markdown(
                        """
                        <div class="obs-table-note">
                            Each row records actor, role, action key, channel, policy rule, reason, queue, priority, and delivery status.
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    preferred_policy_columns = [
                        "created_at",
                        "request_id",
                        "actor",
                        "actor_role",
                        "action_key",
                        "channel",
                        "decision",
                        "policy_rule",
                        "reason",
                        "queue",
                        "priority",
                    ]

                    visible_policy_columns = [
                        col for col in preferred_policy_columns if col in policy_df.columns
                    ]

                    st.dataframe(
                        policy_df[visible_policy_columns],
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info("No outbound policy audit records yet. Approve a ticket to generate policy decisions.")

            with st.container(border=True):
                render_obs_section_header_v2(
                    "09",
                    "Raw Observability JSON",
                    "Developer-friendly API response for debugging and validation.",
                    "Debug view",
                )

                st.markdown(
                    """
                    <div class="obs-json-note">
                        Raw JSON is intentionally collapsed so the page stays clean for screenshots,
                        while still keeping the debugging payload available.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                render_json_panel(
                    "View API Response",
                    obs,
                    expanded=False,
                )
        else:
            render_empty_state(
                "No observability data available",
                "Submit a ticket or run a benchmark to populate observability metrics.",
            )

        st.markdown("</div>", unsafe_allow_html=True)
        

if st.session_state.user_role in {"admin", "ops_analyst"}:
    with tabs[project_overview_tab_index]:
        st.markdown('<div class="project-page-shell">', unsafe_allow_html=True)

        render_section_header(
            "Project Overview",
            "High-level explanation of the workflow, system design, integration options, governance model, and role-based product experience.",
        )

        overview_logs = load_filtered_logs(
            status="All",
            queue="All",
            priority="All",
            search_text="",
            start_date=None,
            end_date=None,
            limit=200,
            offset=0,
        )

        overview_df = pd.DataFrame(overview_logs) if overview_logs else pd.DataFrame()

        if not overview_df.empty:
            overview_metrics = compute_dashboard_metrics(overview_df)
        else:
            overview_metrics = {
                "total_logs": 0,
                "success_rate": 0.0,
                "escalation_rate": 0.0,
                "avg_latency_ms": None,
                "top_queue": "N/A",
            }

        st.markdown(
            """
            <div class="project-intro-panel-v2">
                <div class="project-intro-content">
                    <div class="project-eyebrow">ClaudeOps Flow</div>
                    <div class="project-main-title">
                        AI operations workflow platform for support teams
                    </div>
                    <div class="project-main-text">
                        ClaudeOps Flow turns unstructured support tickets into structured,
                        auditable, automation-ready operational decisions. It combines AI triage,
                        deterministic routing, human approval, policy-based tool access,
                        benchmark analytics, correction feedback, and observability into one
                        SaaS-style workflow.
                    </div>
                    <div class="project-chip-row">
                        <span class="project-chip">▣ FastAPI Backend</span>
                        <span class="project-chip">▦ PostgreSQL Logging</span>
                        <span class="project-chip">◎ LLM Triage</span>
                        <span class="project-chip">🛡 Human Approval</span>
                        <span class="project-chip">↗ Zapier / Make Ready</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        metric_row = st.columns(4)

        with metric_row[0]:
            render_metric_card(
                "Processed Tickets",
                str(overview_metrics["total_logs"]),
                "Demo records created",
                icon="▣",
                tone="blue",
            )

        with metric_row[1]:
            render_metric_card(
                "Success Rate",
                f"{overview_metrics['success_rate']:.1f}%",
                "Workflow reliability",
                icon="✓",
                tone="green",
            )

        with metric_row[2]:
            render_metric_card(
                "Escalation Rate",
                f"{overview_metrics['escalation_rate']:.1f}%",
                "Operational actionability",
                icon="↗",
                tone="orange",
            )

        with metric_row[3]:
            render_metric_card(
                "Avg Latency",
                f"{overview_metrics['avg_latency_ms']:.2f} ms"
                if overview_metrics["avg_latency_ms"] is not None
                else "N/A",
                "Speed of triage",
                icon="◷",
                tone="purple",
            )

        render_section_header(
            "Product Capabilities",
            "The project is designed to look like an operated AI workflow system, not just a single prompt demo.",
        )

        cap_col1, cap_col2, cap_col3 = st.columns(3, gap="medium")

        with cap_col1:
            render_project_capability_card(
                icon="🤖",
                title="AI Triage Engine",
                text=(
                    "Classifies tickets, predicts queue and priority, detects SLA risk, "
                    "extracts structured fields, and generates draft responses through a controlled backend workflow."
                ),
                tone="blue",
            )

        with cap_col2:
            render_project_capability_card(
                icon="🧭",
                title="Deterministic Routing",
                text=(
                    "Uses rule-based pre-routing and specialist prompt profiles so the system is more explainable, "
                    "more consistent, and more cost-efficient than one large generic prompt."
                ),
                tone="purple",
            )

        with cap_col3:
            render_project_capability_card(
                icon="🛡",
                title="Governed Automation",
                text=(
                    "Critical actions wait for human approval, and outbound actions are checked through policy rules "
                    "before Slack, Zapier, Make, or webhook delivery."
                ),
                tone="orange",
            )

        cap_col4, cap_col5, cap_col6 = st.columns(3, gap="medium")

        with cap_col4:
            render_project_capability_card(
                icon="📊",
                title="Observability",
                text=(
                    "Tracks prompt version, model version, token usage, estimated cost, latency, errors, drift alerts, "
                    "and raw trace metadata for production-style monitoring."
                ),
                tone="green",
            )

        with cap_col5:
            render_project_capability_card(
                icon="✎",
                title="Feedback Correction Loop",
                text=(
                    "Allows humans to correct queue, priority, intent, and recommended action, then stores corrections "
                    "back into PostgreSQL for evaluation and benchmark analysis."
                ),
                tone="cyan",
            )

        with cap_col6:
            render_project_capability_card(
                icon="↗",
                title="Cross-Platform Contracts",
                text=(
                    "Publishes a stable outbound automation contract so Zapier, Make, Slack, and webhook integrations "
                    "receive predictable fields and reusable downstream action payloads."
                ),
                tone="red",
            )

        render_section_header(
            "Core Workflow",
            "End-to-end flow from ticket intake to AI triage, approval governance, automation readiness, and monitoring.",
        )

        render_html(
            """
            <div class="project-workflow-panel">
                <div class="project-workflow-grid">
                    <div class="project-workflow-step">
                        <div class="project-step-number">1</div>
                        <div class="project-step-title">Ticket Intake</div>
                        <div class="project-step-text">
                            User submits a support request with subject, body, language, and business context.
                        </div>
                    </div>

                    <div class="project-workflow-step">
                        <div class="project-step-number">2</div>
                        <div class="project-step-title">AI Triage</div>
                        <div class="project-step-text">
                            Backend predicts queue, priority, intent, SLA risk, summary, and recommended action.
                        </div>
                    </div>

                    <div class="project-workflow-step">
                        <div class="project-step-number">3</div>
                        <div class="project-step-title">Approval Gate</div>
                        <div class="project-step-text">
                            Rules decide escalation and approval requirements before external action.
                        </div>
                    </div>

                    <div class="project-workflow-step">
                        <div class="project-step-number">4</div>
                        <div class="project-step-title">Automation Contract</div>
                        <div class="project-step-text">
                            System prepares stable payloads for Slack, Zapier, Make, webhook, Trello, Gmail, or Sheets.
                        </div>
                    </div>

                    <div class="project-workflow-step">
                        <div class="project-step-number">5</div>
                        <div class="project-step-title">Monitoring</div>
                        <div class="project-step-text">
                            PostgreSQL stores traces, cost, feedback, policy audit, benchmark history, and correction data.
                        </div>
                    </div>
                </div>
            </div>
            """
        )

        render_section_header(
            "Technical Architecture",
            "A practical full-stack architecture using FastAPI, PostgreSQL, Streamlit, LLM routing, and workflow integrations.",
        )

        arch_col1, arch_col2 = st.columns(2, gap="medium")

        with arch_col1:
            render_project_architecture_card(
                "Backend Design",
                "FastAPI exposes ticket triage, approvals, policy audit, observability, benchmark, feedback correction, and contract endpoints. PostgreSQL stores triage logs, traces, policy decisions, benchmark runs, feedback corrections, and automation status.",
            )

        with arch_col2:
            render_project_architecture_card(
                "AI Design",
                "The system uses deterministic pre-routing, specialist prompt profiles, structured JSON output, prompt/model version tracking, token usage capture, retry/error handling, and benchmark comparison.",
            )
        
        st.markdown('<div style="height: 0.6rem;"></div>', unsafe_allow_html=True)

        arch_col3, arch_col4 = st.columns(2, gap="medium")

        with arch_col3:
            render_project_architecture_card(
                "Frontend Design",
                "Streamlit provides role-based pages for live ticket submission, operations dashboard, approval queue, integrations, observability, and project overview with reusable UI components and SaaS-style dashboard patterns.",
            )

        with arch_col4:
            render_project_architecture_card(
                "Automation Design",
                "Outbound workflow contracts prepare clean downstream action payloads. A policy engine controls which roles can trigger Slack, Zapier, Make, and external webhook delivery.",
            )

        render_section_header(
            "Role-Based Experience",
            "Admin and Ops Analyst users see different scopes while sharing a consistent product experience.",
        )

        role_col1, role_col2 = st.columns(2, gap="large")

        with role_col1:
            render_role_card_v2(
                icon="🛡",
                title="Admin Workspace",
                text=(
                    "Admins have full access to operational controls, integrations, observability, "
                    "benchmark tools, policy audit, approval execution, and project-level analysis."
                ),
                capabilities=[
                    "Submit tickets",
                    "View operations dashboard",
                    "Approve/reject automations",
                    "Run benchmarks",
                    "View integrations",
                    "View observability",
                    "View policy audit",
                    "View project overview",
                ],
                tone="blue",
            )

        with role_col2:
            render_role_card_v2(
                icon="👥",
                title="Ops Analyst Workspace",
                text=(
                    "Ops Analysts focus on ticket review, operational triage, and controlled approval handling. "
                    "External automation remains governed through policy rules and least-privilege access."
                ),
                capabilities=[
                    "Submit tickets",
                    "View operations dashboard",
                    "Review approval queue",
                    "Approve controlled actions",
                    "External actions policy-governed",
                    "View project overview",
                ],
                tone="orange",
            )

        st.markdown("</div>", unsafe_allow_html=True)