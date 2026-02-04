#!/usr/bin/env python3
# 邮件发送脚本

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys

# 配置
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 587
SENDER_EMAIL = "371398370@qq.com"  # 发件人邮箱
RECEIVER_EMAIL = "371398370@qq.com"  # 收件人邮箱

# 注意：QQ邮箱需要授权码，不是密码
# 发件人需要在QQ邮箱设置中获取授权码
EMAIL_PASSWORD = "hjqibancxrerbifb"  # 需要填写授权码

def send_email(subject, body):
    try:
        # 创建邮件
        message = MIMEMultipart()
        message["From"] = SENDER_EMAIL
        message["To"] = RECEIVER_EMAIL
        message["Subject"] = subject

        # 添加正文
        message.attach(MIMEText(body, "plain", "utf-8"))

        # 创建SSL上下文
        context = ssl.create_default_context()

        # 连接SMTP服务器
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            # 如果没有配置密码，使用空密码尝试
            if EMAIL_PASSWORD:
                server.login(SENDER_EMAIL, EMAIL_PASSWORD)
            else:
                print("警告：未配置邮箱密码/授权码，尝试无认证发送...")
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, message.as_string())

        print(f"邮件发送成功: {subject}")
        return True
    except Exception as e:
        print(f"邮件发送失败: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python3 send_email.py '主题' '正文'")
        sys.exit(1)

    subject = sys.argv[1]
    body = sys.argv[2]
    send_email(subject, body)
