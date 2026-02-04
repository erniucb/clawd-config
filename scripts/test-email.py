#!/usr/bin/env python3
# 测试邮件发送

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 配置
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 587
SENDER_EMAIL = "371398370@qq.com"
RECEIVER_EMAIL = "371398370@qq.com"
EMAIL_PASSWORD = "hjqibancxrerbifb"

def send_test_email():
    try:
        # 创建邮件
        message = MIMEMultipart()
        message["From"] = SENDER_EMAIL
        message["To"] = RECEIVER_EMAIL
        message["Subject"] = "【测试】币圈突破警报系统"

        body = """你好爸爸！

这是来自小桃的测试邮件。

币圈突破警报系统已经配置完成！
- 检测范围：交易量前50币种
- K线周期：4小时
- 突破阈值：1%
- 震荡区间：30根K线

当检测到符合条件的突破时，系统会自动发送警报邮件。

祝爸爸交易顺利！🍑✨

---
发送时间: 2026/02/03
"""

        message.attach(MIMEText(body, "plain", "utf-8"))

        # 创建SSL上下文
        context = ssl.create_default_context()

        # 连接SMTP服务器
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(SENDER_EMAIL, EMAIL_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, message.as_string())

        print("✅ 测试邮件发送成功！")
        return True
    except Exception as e:
        print(f"❌ 邮件发送失败: {str(e)}")
        return False

if __name__ == "__main__":
    send_test_email()
