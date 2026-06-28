import requests
import streamlit as st
from pypinyin import pinyin, Style

import os
from dotenv import load_dotenv

load_dotenv()

WEATHER_KEY = os.getenv("WEATHER_KEY")
AI_KEY = os.getenv("AI_KEY")

st.set_page_config(page_title="AI天气助手", page_icon="🌤️")
st.title("🌤️ AI 智能天气助手")
st.write("输入城市名（中文或拼音都行），AI帮你分析天气、给建议")

city_input = st.text_input("请输入城市名称", value="北京")

if st.button("查天气，听AI建议"):
    if not city_input:
        st.warning("请输入城市名")
    else:
        # 如果输入的是中文，转成拼音
        if any('\u4e00' <= ch <= '\u9fff' for ch in city_input):
            city = ''.join([p[0].capitalize() for p in pinyin(city_input, style=Style.NORMAL)])
            st.info(f"已将「{city_input}」转换为拼音：{city}")
        else:
            city = city_input

        # 1. 获取天气
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_KEY}&lang=zh_cn&units=metric"
        try:
            resp = requests.get(url, timeout=30)
            data = resp.json()
        except requests.exceptions.Timeout:
            st.error("天气服务连接超时，请检查网络或稍后重试")
            st.stop()
        except Exception as e:
            st.error(f"天气查询出错：{e}")
            st.stop()

        if data.get("cod") != 200:
            st.error(f"查询失败：{data.get('message', '未知错误')}")
        else:
            weather = data["weather"][0]["description"]
            temp = data["main"]["temp"]
            humidity = data["main"]["humidity"]
            wind_speed = data["wind"]["speed"]
            weather_info = f"{city_input}今天天气：{weather}，温度：{temp}℃，湿度：{humidity}%，风速：{wind_speed}m/s"

            st.success(f"📡 {weather_info}")

            # 2. 调用AI
            with st.spinner("AI正在思考..."):
                url_ai = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {AI_KEY}"
                }
                payload = {
                    "model": "glm-4-flash",
                    "messages": [
                        {"role": "system", "content": "你是贴心的生活助手，根据天气给穿衣和出行建议，回答简短亲切。"},
                        {"role": "user", "content": f"请根据这个天气给我建议：{weather_info}"}
                    ]
                }

                try:
                    resp_ai = requests.post(url_ai, headers=headers, json=payload, timeout=30)
                    result = resp_ai.json()
                except Exception as e:
                    st.error(f"AI服务连接失败：{e}")
                    st.stop()

                if "error" in result:
                    st.error(f"AI返回错误：{result['error'].get('message', '未知错误')}")
                else:
                    ai_reply = result["choices"][0]["message"]["content"]
                    st.info(f"💡 AI建议：\n{ai_reply}")
