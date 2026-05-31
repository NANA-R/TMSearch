from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from flask import Flask, request
import time
import unicodedata

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--window-size=1920,1080')

app = Flask(__name__)

sbody = """<div style="text-align: center;">"""
ebody = """
       <div style="text-align: center;">
       <form action="/" method="POST">
       <input type="text" name="searchWord"><br>
       <input type="radio" name="sort" value="1" checked>発売日順
       <input type="radio" name="sort" value="2">価格（降順）
       <input type="radio" name="sort" value="3">価格（昇順）<br>
       <input type="submit" value="送信">
       </form>
       </div>
       """
title = """
        <div style = "text-align: center;">
        <h2>検索システム</h2>
        </div>       
        """

def get_east_asian_width(text):
  total_width = 0
  for char in text:
    # 文字の属性を取得 ('W', 'F', 'A' などは全角扱い)
    status = unicodedata.east_asian_width(char)
    if status in ('W', 'F', 'A'):
      total_width += 1.4
    else:
      total_width += 1
  return int(total_width + 0.5)

@app.route("/", methods=["GET", "POST"])
def searching():
  before_word = 0
  if request.method == "GET":
    before_word = "Type here"
    return sbody + title + ebody
  else:
    search_word = request.form.get("searchWord", "")
    if before_word != search_word:
      driver = webdriver.Chrome(options=options)
      products_data = []

      try:
        driver.get("https://www.tokyo-marui.co.jp/")
        time.sleep(3)

        script = """
                var keyword = arguments[0];
                var targets = document.getElementsByName('productname');
                for (var i = 0; i < targets.length; i++) {
                    targets[i].value = keyword;
                    var form = targets[i].closest('form');
                    if (form) { form.submit(); break; }
                }
                """
        driver.execute_script(script, search_word)
        if int(request.form["sort"]) >= 1 and int(request.form["sort"]) <= 3:
          Select(driver.find_element(By.CSS_SELECTOR, "dl dd select")
                 ).select_by_value(request.form["sort"])
      # 検索結果の待機と取得
        for i in range(60):
          items = driver.find_elements(
              By.CSS_SELECTOR, "li.sw-Card_Products-Type1_Item")
          if len(items) > 0 and items[0].text.strip() != "":
            count = 1
            space1 = "0"
            space2 = ""
            space3 = ""
            lenMax = 0
            for item in items:
              try:
                length = get_east_asian_width(
                    item.find_element(By.CSS_SELECTOR, "h3 a").text.strip())
                if lenMax < length:
                  lenMax = length
              except:
                continue
            for item in items:
              try:
                sells = item.find_element(
                    By.CSS_SELECTOR, "span, .category, .type").text.strip()
                name = item.find_element(By.CSS_SELECTOR, "h3 a").text.strip()
                price = item.find_element(
                    By.CSS_SELECTOR, "div p strong").text.strip()
                url = item.find_element(
                    By.CSS_SELECTOR, "a").get_attribute("href")
                category = url.split("/")[-3]
                if category == "electric":
                  category = "電動ガン"
                elif category == "gas":
                  category = "ガスガン"
                elif category == "aircocking":
                  category = "エアコキ"
                else:
                  category = "Unknown"

                if search_word in name:
                  if count >= 10:
                    space1 = ""
                  if sells == "発売中":
                    space2 = "⠀"
                  else:
                    space2 = ""
                  tmp = lenMax - get_east_asian_width(name)
                  if tmp == 0:
                    space3 = "⠀"
                  else:
                    space3 = "⠀" * (tmp + 1)
                  products_data.append(
                      f"""{space1}{count}. 【{sells}】{space2}[{category}]{name}{space3} | {price}{type(price)} <a href="{url}">製品リンク</a>""")
                  count += 1
              except:
                print("ERROR")
            break
          time.sleep(0.5)
        driver.quit()  # 解析が終わってから閉じる

        if products_data:
          result_text = "<br>".join(products_data)
        else:
          result_text = "該当なし"

        return sbody + f"""
                <h3>「{search_word}」の検索結果</h3>
                </div>
                <div style="display: flex;">
                <p>{result_text}</p>
                </div>
                <hr>
                """ + ebody

      except Exception as e:
        if 'driver' in locals():
          driver.quit()
        return f"エラーが発生しました: {e}"
    else:
      pass

if __name__ == '__main__':
  app.run(debug=True)
