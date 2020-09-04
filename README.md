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
    ./manage.py loaddata campuses faculties admission_projects_and_rounds majors
```
