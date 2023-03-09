# คู่มืออย่างย่อ

หมายเหตุ: อ่านคู่มือเต็มได้ที่ wiki บน GitHub

## ติดตั้ง

หลังจากลง Django เรียบร้อยแล้ว จึงติดตั้ง requirement เพิ่มเติมของ project นี้ด้วย pip

    pip install -r requirements.txt

หลังจากนั้น นำเข้าข้อมูลเริ่มต้นใน fixtures

```
    ./manage.py makemigrations
    ./manage.py migrate
    ./manage.py migrate --run-syncdb
    ./manage.py loaddata campuses faculties majors provinces admission_rounds
```
## ใช้ pipenv
สร้าง env และ install dependencies สำหรับทำครั้งแรก
```
    pipenv --python 3
    pipenv install --dev
```
สำหรับเปิด shell เพื่อเข้าไปรันคำสั่ง manage.py ต่างๆ
```
    pipenv shell
```


## ใช้ conda
**สร้าง env ครั้งแรก**
```shell
conda create -n admapp python=3.8
```
**Activate**
```shell
conda activate admapp
```
**Install requirements**
```shell
pip install -r requirements.txt
```

## MySql
ถ้าต้องการใช้ MySql สำหรับ develop สามารถรัน `docker-compose.yml` และตั้งค่า `/admapp/settings_local.py` เพิมเติมได้
```shell
docker-compose up
```

### Setup ครั้งแรก
1. เข้า phpMyAdmin http://localhost:8080/  
2. สร้าง database admapp
3. import database (ขอจากคนอื่น)
4. แก้ `/admapp/settings_local.py` ให้ใช้ mysql database
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'admapp',
        'USER': 'root',
        'PASSWORD': 'example',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}
```
