# Per story

## h01 — ตั้งวงกับเพื่อนที่ร้านหมูกระทะ ตอนกลับก็ขับเองเพราะคิดว่ายังไหว
gold: `violations_found` ['drunk']  
- **agent** ✗ `need_more_info` []
- **baseline** ✗ `no_violation` []

## h02 — ขับรถแชทไลน์ไปด้วย มือถือไว้มือนึง
gold: `violations_found` ['phone']  
- **agent** ✓ `violations_found` ['phone']
- **baseline** ✓ `violations_found` ['phone']

## h03 — เข้าซอยที่มีป้ายห้ามเข้า สวนทางรถคนอื่นออกมา
gold: `violations_found` ['wrong_way']  
- **agent** ✗ `violations_found` ['no_plate']
- **baseline** ✓ `violations_found` ['wrong_way']

## h04 — บิ๊กไบค์ซิ่งเกินสองร้อย ไม่ใส่หมวก ปาดหน้าคันอื่นจนเขาต้องเบรก
gold: `violations_found` ['speeding', 'no_helmet', 'reckless']  
- **agent** ✓ `violations_found` ['no_helmet', 'reckless', 'speeding']
- **baseline** ✓ `violations_found` ['no_helmet', 'reckless', 'speeding']

## h05 — เมาแล้วขับไปชนมอไซค์คนอื่นล้ม แล้วตกใจหนีไป
gold: `violations_found` ['drunk', 'hit_and_run']  
- **agent** ✓ `violations_found` ['drunk', 'hit_and_run']
- **baseline** ✓ `violations_found` ['drunk', 'hit_and_run']

## h06 — พาลูกเล็กนั่งเบาะหน้าไม่มีเบาะเด็ก แล้วได้ยินเสียงหวอข้างหลังก็ไม่ยอมหลบ
gold: `violations_found` ['no_seatbelt', 'emergency_no_yield']  
- **agent** ✓ `violations_found` ['emergency_no_yield', 'no_seatbelt']
- **baseline** ✗ `violations_found` ['no_regard_safety', 'no_seatbelt']

## h07 — รอไฟแดงจนเขียวแล้วค่อยออกตัว ใส่หมวกเรียบร้อย
gold: `no_violation` []  
- **agent** ✓ `no_violation` []
- **baseline** ✓ `no_violation` []

## h08 — ไม่ได้กินเหล้าเลยแม้แต่แก้วเดียวก่อนขับ
gold: `no_violation` []  
- **agent** ✓ `no_violation` []
- **baseline** ✓ `no_violation` []

## h09 — ตำรวจบอกว่าผมผิดกฎจราจร แต่ไม่ได้บอกว่าเรื่องอะไร
gold: `need_more_info` []  
- **agent** ✓ `need_more_info` []
- **baseline** ✓ `need_more_info` []

## h10 — จอดรถในที่ห้ามจอดหน้าโรงพยาบาล
gold: `out_of_scope` []  
- **agent** ✓ `out_of_scope` []
- **baseline** ✓ `out_of_scope` []
