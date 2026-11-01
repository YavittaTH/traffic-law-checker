# Per story

## s01 — เมื่อคืนปาร์ตี้วันเกิดเพื่อน หมดไปหลายขวด ตีสองก็ขับกลับเอง
gold: `violations_found` ['drunk']  
- **rag** ✗ `violations_found` ['impaired']

## s02 — ขับรถคุยโทรสับไปด้วย ถือไว้ข้างหู
gold: `violations_found` ['phone']  
- **rag** ✓ `violations_found` ['phone']

## s03 — ไฟเขียวกระพริบ เหลือง แล้วก็แดง แต่ผมเร่งตามคันหน้าไปติดๆ
gold: `violations_found` ['red_light']  
- **rag** ✗ `no_violation` []

## s04 — ขี่รถเครื่องไปตลาดใกล้ๆ ขี้เกียจใส่หมวก
gold: `violations_found` ['no_helmet']  
- **rag** ✓ `violations_found` ['no_helmet']

## s05 — รถติดมาก เลยขี่ขึ้นไปบนทางที่คนเดินแป๊บเดียว
gold: `violations_found` ['sidewalk']  
- **rag** ✗ `out_of_scope` []

## s06 — ขับมาเกือบร้อยหกสิบ ถนนเส้นนั้นเขาให้ร้อยยี่สิบ
gold: `violations_found` ['speeding']  
- **rag** ✗ `no_violation` []

## s07 — มีคนยืนรอข้ามตรงแถบขาวดำ แต่ผมไม่ชะลอ ขับผ่านไปเลย
gold: `violations_found` ['crosswalk_no_stop']  
- **rag** ✓ `violations_found` ['crosswalk_no_stop']

## s08 — เฉี่ยวกระจกข้างรถคันอื่นแล้วตกใจ เลยรีบไปต่อไม่ได้จอด
gold: `violations_found` ['hit_and_run']  
- **rag** ✓ `violations_found` ['hit_and_run']

## s09 — นั่งหลังพวงมาลัยทั้งที่ไม่ได้รัดอะไรเลย
gold: `violations_found` ['no_seatbelt']  
- **rag** ✓ `violations_found` ['no_seatbelt']

## s10 — ทะเบียนหลุดหายไปตั้งแต่อาทิตย์ก่อน ยังขับใช้ปกติ
gold: `violations_found` ['no_plate']  
- **rag** ✓ `violations_found` ['no_plate']

## s11 — ลูกสามขวบนั่งตักแม่ที่เบาะหน้า ไม่มีคาร์ซีท ผมขับเองก็ไม่ได้คาด
gold: `violations_found` ['no_seatbelt']  
- **rag** ✓ `violations_found` ['no_seatbelt']

## s12 — ขี่มอไซค์ซ้อนแฟนไปกินข้าว ทั้งคู่ไม่มีหมวก
gold: `violations_found` ['no_helmet', 'no_helmet_passenger']  
- **rag** ✓ `violations_found` ['no_helmet', 'no_helmet_passenger']

## s13 — กินเบียร์มาสามกระป๋อง ขับกลับไวๆ ประมาณ 140 ในเมือง
gold: `violations_found` ['drunk', 'speeding']  
- **rag** ✗ `violations_found` ['drunk', 'impaired', 'speeding']

## s14 — เลี้ยวเข้าซอยวันเวย์แบบทวนทาง แล้วคุยไลน์ไปด้วย
gold: `violations_found` ['wrong_way', 'phone']  
- **rag** ✓ `violations_found` ['phone', 'wrong_way']

## s15 — โดนตำรวจเรียกตรวจ เป่าแล้วเกิน แถมไม่ได้คาดเข็มขัด
gold: `violations_found` ['drunk', 'no_seatbelt']  
- **rag** ✗ `violations_found` ['no_seatbelt']

## s16 — ทำงานสองกะติดกันจนหลับใน ไปชนเสาไฟข้างทาง แล้วก็ขับต่อไปเลยไม่ได้แจ้งใคร
gold: `violations_found` ['impaired', 'hit_and_run']  
- **rag** ✓ `violations_found` ['hit_and_run', 'impaired']

## s17 — รถพยาบาลเปิดไฟมาข้างหลังแต่ไม่หลบ แถมฝ่าแดงหนีไปอีก
gold: `violations_found` ['emergency_no_yield', 'red_light']  
- **rag** ✓ `violations_found` ['emergency_no_yield', 'red_light']

## s18 — ขี่มอไซค์ไม่ใส่หมวกขึ้นฟุตปาธ ขับปาดซ้ายปาดขวา
gold: `violations_found` ['no_helmet', 'sidewalk', 'reckless']  
- **rag** ✓ `violations_found` ['no_helmet', 'reckless', 'sidewalk']

## s19 — เสพยามาแล้วรวมแก๊งแข่งรถบนถนนเลียบทางด่วนตอนตีสาม
gold: `violations_found` ['drugs', 'street_racing']  
- **rag** ✓ `violations_found` ['drugs', 'street_racing']

## s20 — ขับรถส่ายไปมาเบียดคันอื่น เพราะมัวแต่ก้มดูมือถือ
gold: `violations_found` ['reckless', 'phone']  
- **rag** ✗ `violations_found` ['reckless']

## s21 — ใส่หมวกครบทั้งคนขี่คนซ้อน ขับชิดซ้าย ความเร็วไม่เกินที่ป้ายบอก
gold: `no_violation` []  
- **rag** ✓ `no_violation` []

## s22 — คุยโทรศัพท์ผ่านหูฟังบลูทูธ มือจับพวงมาลัยตลอด ไม่ได้ถือเครื่อง
gold: `no_violation` []  
- **rag** ✓ `no_violation` []

## s23 — หยุดให้คนข้ามทางม้าลายจนข้ามเสร็จแล้วค่อยไปต่อ
gold: `no_violation` []  
- **rag** ✓ `no_violation` []

## s24 — ดื่มน้ำอัดลมกับเพื่อนแล้วขับกลับ ไม่ได้แตะแอลกอฮอล์เลย
gold: `no_violation` []  
- **rag** ✓ `no_violation` []

## s25 — ขับรถอยู่ดีๆ โดนตำรวจโบกให้จอด ผิดอะไรเหรอ
gold: `need_more_info` []  
- **rag** ✗ `no_violation` []

## s26 — ขับเร็วไปหน่อยตอนกลับบ้าน
gold: `need_more_info` []  
- **rag** ✗ `violations_found` ['speeding']

## s27 — ชนท้ายรถคันหน้าเบาๆ ตอนรถติด
gold: `need_more_info` []  
- **rag** ✗ `no_violation` []

## s28 — จอดรถซ้อนคันหน้าห้างนานครึ่งชั่วโมง
gold: `out_of_scope` []  
- **rag** ✗ `no_violation` []

## s29 — ภาษีรถขาดมาสองปีแล้วยังขับอยู่
gold: `out_of_scope` []  
- **rag** ✓ `out_of_scope` []

## s30 — ขับรถมาหลายปีทั้งที่ไม่เคยสอบใบขับขี่เลย
gold: `out_of_scope` []  
- **rag** ✗ `violations_found` ['impaired']

## s31 — ขับรถตอนกลางคืนไม่เปิดไฟหน้า
gold: `out_of_scope` []  
- **rag** ✗ `violations_found` ['abnormal_driving']
