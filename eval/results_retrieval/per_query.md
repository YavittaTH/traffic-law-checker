# Per query (modes: bm25_raw and bm25)

- **d01** [bm25_raw] ขับรถคุยมือถือไปด้วย ถือโทรศัพท์แนบหู  
  expected ['43'] → top5 ['91', '142/5', '39', '125', '142/3'] ✗ missing 43
- **d02** [bm25_raw] ขี่มอไซค์ไม่ได้ใส่หมวกกันน็อค  
  expected ['122'] → top5 ['122', '11', '111', '78', '112'] ✓
- **d03** [bm25_raw] เมื่อคืนกินเหล้าไปหลายแก้วแล้วขับรถกลับบ้าน  
  expected ['43'] → top5 ['128', '39', '125', '142/3', '74'] ✗ missing 43
- **d04** [bm25_raw] ฝ่าไฟแดงตรงสี่แยก  
  expected ['22'] → top5 ['24', '20', '37'] ✗ missing 22
- **d05** [bm25_raw] ขับย้อนศรเพราะขี้เกียจไปกลับรถไกล  
  expected ['33'] → top5 ['53', '49', '11', '68', '83'] ✗ missing 33
- **d06** [bm25_raw] ขี่มอไซค์ขึ้นฟุตบาทหนีรถติด  
  expected ['43'] → top5 ['111', '78', '112', '76', '41'] ✗ missing 43
- **d07** [bm25_raw] เห็นคนจะข้ามทางม้าลายแต่ไม่ได้หยุดรถ  
  expected ['21'] → top5 ['105', '106', '4', '51', '22'] ✗ missing 21
- **d08** [bm25_raw] ขับรถชนรถคันหน้าแล้วขับหนีไปเลย  
  expected ['78'] → top5 ['83', '44', '123/2', '49', '40'] ✗ missing 78
- **d09** [bm25_raw] ไม่คาดเข็มขัดนิรภัยตอนขับรถ  
  expected ['123'] → top5 ['123', '123/1', '123/2', '138', '20'] ✓
- **d10** [bm25_raw] รถพยาบาลเปิดหวอมาข้างหลังแต่ไม่หลบให้  
  expected ['76'] → top5 ['49', '4', '36', '76'] ✓
- **d11** [bm25_raw] ขับ 140 บนถนนที่ป้ายบอก 90  
  expected ['67'] → top5 ['72', '7', '93', '11', '90'] ✗ missing 67
- **d12** [bm25_raw] เด็กแว้นรวมกลุ่มแข่งรถกันบนถนนตอนดึก  
  expected ['134'] → top5 ['134', '160เบญจ', '72', '123', '32'] ✓
- **d13** [bm25_raw] ง่วงมากแทบหลับในแต่ยังฝืนขับต่อ  
  expected ['43'] → top5 ['83', '79', '117', '44', '49'] ✗ missing 43
- **d14** [bm25_raw] ได้ใบสั่งมาแล้วไม่ไปจ่ายค่าปรับ  
  expected ['141'] → top5 ['141', '13', '141/1', '140', '14'] ✓
- **d15** [bm25_raw] ขี่มอไซค์ซ้อนท้ายแฟน คนซ้อนไม่ใส่หมวก แล้วฝ่าไฟแดง  
  expected ['122', '22'] → top5 ['122', '20', '11', '121', '24'] ✗ missing 22
- **d16** [bm25_raw] เมาแล้วขับรถเร็ว ไม่คาดเข็มขัด  
  expected ['123', '43', '67'] → top5 ['142', '11', '43', '83', '39'] ✗ missing 123, 67
- **d17** [bm25_raw] ขับรถไม่มีป้ายทะเบียน  
  expected ['7'] → top5 ['7', '93', '9', '11', '72'] ✓
- **d18** [bm25_raw] เสพยาบ้าแล้วขับรถบรรทุก  
  expected ['43ทวิ'] → top5 ['43ทวิ', '16', '20', '11', '83'] ✓
- **d01** [bm25] ขับรถคุยมือถือไปด้วย ถือโทรศัพท์แนบหู  
  expected ['43'] → top5 ['91', '43', '142/5', '11', '39'] ✓
- **d02** [bm25] ขี่มอไซค์ไม่ได้ใส่หมวกกันน็อค  
  expected ['122'] → top5 ['122', '11', '12', '20', '123'] ✓
- **d03** [bm25] เมื่อคืนกินเหล้าไปหลายแก้วแล้วขับรถกลับบ้าน  
  expected ['43'] → top5 ['142', '11', '43', '83', '128'] ✓
- **d04** [bm25] ฝ่าไฟแดงตรงสี่แยก  
  expected ['22'] → top5 ['22', '23', '38', '106', '20'] ✓
- **d05** [bm25] ขับย้อนศรเพราะขี้เกียจไปกลับรถไกล  
  expected ['33'] → top5 ['53', '49', '52', '20', '68'] ✗ missing 33
- **d06** [bm25] ขี่มอไซค์ขึ้นฟุตบาทหนีรถติด  
  expected ['43'] → top5 ['11', '122', '103', '121', '41'] ✗ missing 43
- **d07** [bm25] เห็นคนจะข้ามทางม้าลายแต่ไม่ได้หยุดรถ  
  expected ['21'] → top5 ['106', '105', '104', '4', '145'] ✗ missing 21
- **d08** [bm25] ขับรถชนรถคันหน้าแล้วขับหนีไปเลย  
  expected ['78'] → top5 ['78', '83', '11', '142/5', '44'] ✓
- **d09** [bm25] ไม่คาดเข็มขัดนิรภัยตอนขับรถ  
  expected ['123'] → top5 ['123', '11', '123/1', '123/2', '20'] ✓
- **d10** [bm25] รถพยาบาลเปิดหวอมาข้างหลังแต่ไม่หลบให้  
  expected ['76'] → top5 ['4', '76', '49', '74', '127'] ✓
- **d11** [bm25] ขับ 140 บนถนนที่ป้ายบอก 90  
  expected ['67'] → top5 ['67', '72', '90', '96', '75'] ✓
- **d12** [bm25] เด็กแว้นรวมกลุ่มแข่งรถกันบนถนนตอนดึก  
  expected ['134'] → top5 ['134', '160เบญจ', '11', '72', '123'] ✓
- **d13** [bm25] ง่วงมากแทบหลับในแต่ยังฝืนขับต่อ  
  expected ['43'] → top5 ['43', '142', '11', '49', '83'] ✓
- **d14** [bm25] ได้ใบสั่งมาแล้วไม่ไปจ่ายค่าปรับ  
  expected ['141'] → top5 ['141', '13', '141/1', '140', '14'] ✓
- **d15** [bm25] ขี่มอไซค์ซ้อนท้ายแฟน คนซ้อนไม่ใส่หมวก แล้วฝ่าไฟแดง  
  expected ['122', '22'] → top5 ['122', '11', '22', '20', '121'] ✓
- **d16** [bm25] เมาแล้วขับรถเร็ว ไม่คาดเข็มขัด  
  expected ['123', '43', '67'] → top5 ['142', '123', '67', '43', '83'] ✓
- **d17** [bm25] ขับรถไม่มีป้ายทะเบียน  
  expected ['7'] → top5 ['7', '11', '93', '72', '17'] ✓
- **d18** [bm25] เสพยาบ้าแล้วขับรถบรรทุก  
  expected ['43ทวิ'] → top5 ['43ทวิ', '11', '157/1', '17', '16'] ✓
- **d01** [offense:bm25] ขับรถคุยมือถือไปด้วย ถือโทรศัพท์แนบหู  
  expected ['phone'] → top5 ['phone', 'abnormal_driving', 'suspended_license', 'drunk', 'speeding'] ✓
- **d02** [offense:bm25] ขี่มอไซค์ไม่ได้ใส่หมวกกันน็อค  
  expected ['no_helmet'] → top5 ['no_helmet', 'no_helmet_passenger', 'reckless', 'hit_and_run'] ✓
- **d03** [offense:bm25] เมื่อคืนกินเหล้าไปหลายแก้วแล้วขับรถกลับบ้าน  
  expected ['drunk'] → top5 ['drunk', 'abnormal_driving', 'suspended_license', 'speeding', 'impaired'] ✓
- **d04** [offense:bm25] ฝ่าไฟแดงตรงสี่แยก  
  expected ['red_light'] → top5 ['red_light', 'crosswalk_no_stop', 'speeding', 'emergency_no_yield', 'hit_and_run'] ✓
- **d05** [offense:bm25] ขับย้อนศรเพราะขี้เกียจไปกลับรถไกล  
  expected ['wrong_way'] → top5 ['wrong_way', 'no_plate', 'impaired', 'crosswalk_no_stop', 'no_seatbelt'] ✓
- **d06** [offense:bm25] ขี่มอไซค์ขึ้นฟุตบาทหนีรถติด  
  expected ['sidewalk'] → top5 ['sidewalk', 'no_helmet', 'no_helmet_passenger', 'hit_and_run', 'abnormal_driving'] ✓
- **d07** [offense:bm25] เห็นคนจะข้ามทางม้าลายแต่ไม่ได้หยุดรถ  
  expected ['crosswalk_no_stop'] → top5 ['crosswalk_no_stop', 'emergency_no_yield', 'hit_and_run', 'red_light', 'no_plate'] ✓
- **d08** [offense:bm25] ขับรถชนรถคันหน้าแล้วขับหนีไปเลย  
  expected ['hit_and_run'] → top5 ['hit_and_run', 'impaired', 'reckless', 'no_seatbelt', 'emergency_no_yield'] ✓
- **d09** [offense:bm25] ไม่คาดเข็มขัดนิรภัยตอนขับรถ  
  expected ['no_seatbelt'] → top5 ['no_seatbelt', 'no_regard_safety', 'abnormal_driving', 'suspended_license', 'drunk'] ✓
- **d10** [offense:bm25] รถพยาบาลเปิดหวอมาข้างหลังแต่ไม่หลบให้  
  expected ['emergency_no_yield'] → top5 ['emergency_no_yield'] ✓
- **d11** [offense:bm25] ขับ 140 บนถนนที่ป้ายบอก 90  
  expected ['speeding'] → top5 ['speeding', 'plate_incomplete', 'impaired', 'no_plate', 'red_light'] ✓
- **d12** [offense:bm25] เด็กแว้นรวมกลุ่มแข่งรถกันบนถนนตอนดึก  
  expected ['street_racing'] → top5 ['street_racing', 'no_helmet', 'no_helmet_passenger', 'no_seatbelt', 'wrong_way'] ✓
- **d13** [offense:bm25] ง่วงมากแทบหลับในแต่ยังฝืนขับต่อ  
  expected ['impaired'] → top5 ['impaired', 'no_seatbelt', 'abnormal_driving', 'suspended_license', 'drunk'] ✓
- **d14** [offense:bm25] ได้ใบสั่งมาแล้วไม่ไปจ่ายค่าปรับ  
  expected ['unpaid_ticket'] → top5 ['unpaid_ticket'] ✓
- **d15** [offense:bm25] ขี่มอไซค์ซ้อนท้ายแฟน คนซ้อนไม่ใส่หมวก แล้วฝ่าไฟแดง  
  expected ['no_helmet_passenger', 'red_light'] → top5 ['no_helmet_passenger', 'no_helmet', 'red_light', 'crosswalk_no_stop', 'hit_and_run'] ✓
- **d16** [offense:bm25] เมาแล้วขับรถเร็ว ไม่คาดเข็มขัด  
  expected ['drunk', 'no_seatbelt', 'speeding'] → top5 ['drunk', 'speeding', 'no_seatbelt', 'no_regard_safety', 'red_light'] ✓
- **d17** [offense:bm25] ขับรถไม่มีป้ายทะเบียน  
  expected ['no_plate'] → top5 ['no_plate', 'plate_incomplete', 'abnormal_driving', 'suspended_license', 'drunk'] ✓
- **d18** [offense:bm25] เสพยาบ้าแล้วขับรถบรรทุก  
  expected ['drugs'] → top5 ['drugs', 'impaired', 'no_seatbelt', 'abnormal_driving', 'suspended_license'] ✓
