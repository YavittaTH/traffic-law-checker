# Per query (modes: bm25_raw and hybrid)

- **s01** [bm25_raw] เมื่อคืนปาร์ตี้วันเกิดเพื่อน หมดไปหลายขวด ตีสองก็ขับกลับเอง  
  expected ['43'] → top5 ['83', '79', '117', '44', '49'] ✗ missing 43
- **s02** [bm25_raw] ขับรถคุยโทรสับไปด้วย ถือไว้ข้างหู  
  expected ['43'] → top5 ['91', '39', '125', '142/3', '74'] ✗ missing 43
- **s03** [bm25_raw] ไฟเขียวกระพริบ เหลือง แล้วก็แดง แต่ผมเร่งตามคันหน้าไปติดๆ  
  expected ['22'] → top5 ['38', '44', '40', '90', '15'] ✗ missing 22
- **s04** [bm25_raw] ขี่รถเครื่องไปตลาดใกล้ๆ ขี้เกียจใส่หมวก  
  expected ['122'] → top5 ['122', '11', '111', '78', '112'] ✓
- **s05** [bm25_raw] รถติดมาก เลยขี่ขึ้นไปบนทางที่คนเดินแป๊บเดียว  
  expected ['43'] → top5 ['76', '35', '34', '4', '66'] ✗ missing 43
- **s06** [bm25_raw] ขับมาเกือบร้อยหกสิบ ถนนเส้นนั้นเขาให้ร้อยยี่สิบ  
  expected ['67'] → top5 ['130', '72', '147', '35', '145'] ✗ missing 67
- **s07** [bm25_raw] มีคนยืนรอข้ามตรงแถบขาวดำ แต่ผมไม่ชะลอ ขับผ่านไปเลย  
  expected ['21'] → top5 ['105', '4', '106', '124', '83'] ✗ missing 21
- **s08** [bm25_raw] เฉี่ยวกระจกข้างรถคันอื่นแล้วตกใจ เลยรีบไปต่อไม่ได้จอด  
  expected ['78'] → top5 ['90', '76', '36', '54', '60'] ✗ missing 78
- **s09** [bm25_raw] นั่งหลังพวงมาลัยทั้งที่ไม่ได้รัดอะไรเลย  
  expected ['123'] → top5 ['123', '123/1', '121', '123/2', '20'] ✓
- **s10** [bm25_raw] ทะเบียนหลุดหายไปตั้งแต่อาทิตย์ก่อน ยังขับใช้ปกติ  
  expected ['7'] → top5 ['9', '83', '79', '117', '44'] ✗ missing 7
- **s11** [bm25_raw] ลูกสามขวบนั่งตักแม่ที่เบาะหน้า ไม่มีคาร์ซีท ผมขับเองก็ไม่ได้คาด  
  expected ['123'] → top5 ['123/2', '83', '123', '160ตรี/2', '121'] ✓
- **s12** [bm25_raw] ขี่มอไซค์ซ้อนแฟนไปกินข้าว ทั้งคู่ไม่มีหมวก  
  expected ['122'] → top5 ['122', '11', '111', '78', '112'] ✓
- **s13** [bm25_raw] กินเบียร์มาสามกระป๋อง ขับกลับไวๆ ประมาณ 140 ในเมือง  
  expected ['43', '67'] → top5 ['128', '140/1', '83', '150', '140/2'] ✗ missing 43, 67
- **s14** [bm25_raw] เลี้ยวเข้าซอยวันเวย์แบบทวนทาง แล้วคุยไลน์ไปด้วย  
  expected ['33', '43'] → top5 ['91', '51', '38', '72', '22'] ✗ missing 33, 43
- **s15** [bm25_raw] โดนตำรวจเรียกตรวจ เป่าแล้วเกิน แถมไม่ได้คาดเข็มขัด  
  expected ['123', '43'] → top5 ['43ทวิ/1', '32', '40', '31/1', '123/1'] ✗ missing 123, 43
- **s16** [bm25_raw] ทำงานสองกะติดกันจนหลับใน ไปชนเสาไฟข้างทาง แล้วก็ขับต่อไปเลยไม่ได้แจ้งใคร  
  expected ['43', '78'] → top5 ['103', '162', '141/1', '23', '160จัตวา'] ✗ missing 43, 78
- **s17** [bm25_raw] รถพยาบาลเปิดไฟมาข้างหลังแต่ไม่หลบ แถมฝ่าแดงหนีไปอีก  
  expected ['22', '76'] → top5 ['15', '20', '11', '61', '81'] ✗ missing 22, 76
- **s18** [bm25_raw] ขี่มอไซค์ไม่ใส่หมวกขึ้นฟุตปาธ ขับปาดซ้ายปาดขวา  
  expected ['122', '43'] → top5 ['44', '122', '76', '73', '51'] ✗ missing 43
- **s19** [bm25_raw] เสพยามาแล้วรวมแก๊งแข่งรถบนถนนเลียบทางด่วนตอนตีสาม  
  expected ['134', '43ทวิ'] → top5 ['43ทวิ', '11', '134', '160เบญจ', '72'] ✓
- **s20** [bm25_raw] ขับรถส่ายไปมาเบียดคันอื่น เพราะมัวแต่ก้มดูมือถือ  
  expected ['43'] → top5 ['40', '90', '39', '95', '48'] ✗ missing 43
- **s01** [hybrid] เมื่อคืนปาร์ตี้วันเกิดเพื่อน หมดไปหลายขวด ตีสองก็ขับกลับเอง  
  expected ['43'] → top5 ['142', '11', '83', '20', '20'] ✗ missing 43
- **s02** [hybrid] ขับรถคุยโทรสับไปด้วย ถือไว้ข้างหู  
  expected ['43'] → top5 ['91', '125', '43', '39', '140/2'] ✓
- **s03** [hybrid] ไฟเขียวกระพริบ เหลือง แล้วก็แดง แต่ผมเร่งตามคันหน้าไปติดๆ  
  expected ['22'] → top5 ['38', '15', '44', '20', '105'] ✗ missing 22
- **s04** [hybrid] ขี่รถเครื่องไปตลาดใกล้ๆ ขี้เกียจใส่หมวก  
  expected ['122'] → top5 ['122', '78', '11', '50', '4'] ✓
- **s05** [hybrid] รถติดมาก เลยขี่ขึ้นไปบนทางที่คนเดินแป๊บเดียว  
  expected ['43'] → top5 ['41', '35', '4', '76', '48'] ✗ missing 43
- **s06** [hybrid] ขับมาเกือบร้อยหกสิบ ถนนเส้นนั้นเขาให้ร้อยยี่สิบ  
  expected ['67'] → top5 ['69', '79', '160เบญจ', '70', '20'] ✗ missing 67
- **s07** [hybrid] มีคนยืนรอข้ามตรงแถบขาวดำ แต่ผมไม่ชะลอ ขับผ่านไปเลย  
  expected ['21'] → top5 ['105', '106', '24', '4', '107'] ✗ missing 21
- **s08** [hybrid] เฉี่ยวกระจกข้างรถคันอื่นแล้วตกใจ เลยรีบไปต่อไม่ได้จอด  
  expected ['78'] → top5 ['76', '68', '36', '20', '50'] ✗ missing 78
- **s09** [hybrid] นั่งหลังพวงมาลัยทั้งที่ไม่ได้รัดอะไรเลย  
  expected ['123'] → top5 ['123', '123/1', '121', '11', '123/2'] ✓
- **s10** [hybrid] ทะเบียนหลุดหายไปตั้งแต่อาทิตย์ก่อน ยังขับใช้ปกติ  
  expected ['7'] → top5 ['20', '11', '9', '142/7', '83'] ✗ missing 7
- **s11** [hybrid] ลูกสามขวบนั่งตักแม่ที่เบาะหน้า ไม่มีคาร์ซีท ผมขับเองก็ไม่ได้คาด  
  expected ['123'] → top5 ['123', '123/2', '89', '123/1', '94'] ✓
- **s12** [hybrid] ขี่มอไซค์ซ้อนแฟนไปกินข้าว ทั้งคู่ไม่มีหมวก  
  expected ['122'] → top5 ['122', '121', '78', '41', '11'] ✓
- **s13** [hybrid] กินเบียร์มาสามกระป๋อง ขับกลับไวๆ ประมาณ 140 ในเมือง  
  expected ['43', '67'] → top5 ['142', '11', '156', '83', '160ตรี'] ✗ missing 43, 67
- **s14** [hybrid] เลี้ยวเข้าซอยวันเวย์แบบทวนทาง แล้วคุยไลน์ไปด้วย  
  expected ['33', '43'] → top5 ['41', '33', '51', '20', '34'] ✗ missing 43
- **s15** [hybrid] โดนตำรวจเรียกตรวจ เป่าแล้วเกิน แถมไม่ได้คาดเข็มขัด  
  expected ['123', '43'] → top5 ['43ทวิ/1', '11', '123/1', '142/6', '123'] ✗ missing 43
- **s16** [hybrid] ทำงานสองกะติดกันจนหลับใน ไปชนเสาไฟข้างทาง แล้วก็ขับต่อไปเลยไม่ได้แจ้งใคร  
  expected ['43', '78'] → top5 ['22', '38', '141/1', '160จัตวา', '23'] ✗ missing 43, 78
- **s17** [hybrid] รถพยาบาลเปิดไฟมาข้างหลังแต่ไม่หลบ แถมฝ่าแดงหนีไปอีก  
  expected ['22', '76'] → top5 ['76', '24', '20', '78', '15'] ✗ missing 22
- **s18** [hybrid] ขี่มอไซค์ไม่ใส่หมวกขึ้นฟุตปาธ ขับปาดซ้ายปาดขวา  
  expected ['122', '43'] → top5 ['122', '83', '103', '20', '47'] ✗ missing 43
- **s19** [hybrid] เสพยามาแล้วรวมแก๊งแข่งรถบนถนนเลียบทางด่วนตอนตีสาม  
  expected ['134', '43ทวิ'] → top5 ['43ทวิ', '134', '11', '160เบญจ', '157/1'] ✓
- **s20** [hybrid] ขับรถส่ายไปมาเบียดคันอื่น เพราะมัวแต่ก้มดูมือถือ  
  expected ['43'] → top5 ['43', '39', '40', '20', '11'] ✓
- **s01** [offense:hybrid] เมื่อคืนปาร์ตี้วันเกิดเพื่อน หมดไปหลายขวด ตีสองก็ขับกลับเอง  
  expected ['drunk'] → top5 ['impaired', 'no_seatbelt', 'drunk', 'hit_and_run', 'no_regard_safety'] ✓
- **s02** [offense:hybrid] ขับรถคุยโทรสับไปด้วย ถือไว้ข้างหู  
  expected ['phone'] → top5 ['phone', 'suspended_license', 'abnormal_driving', 'drunk', 'impaired'] ✓
- **s03** [offense:hybrid] ไฟเขียวกระพริบ เหลือง แล้วก็แดง แต่ผมเร่งตามคันหน้าไปติดๆ  
  expected ['red_light'] → top5 ['no_seatbelt', 'red_light', 'crosswalk_no_stop', 'emergency_no_yield', 'hit_and_run'] ✓
- **s04** [offense:hybrid] ขี่รถเครื่องไปตลาดใกล้ๆ ขี้เกียจใส่หมวก  
  expected ['no_helmet'] → top5 ['no_helmet', 'no_helmet_passenger', 'hit_and_run', 'sidewalk', 'no_seatbelt'] ✓
- **s05** [offense:hybrid] รถติดมาก เลยขี่ขึ้นไปบนทางที่คนเดินแป๊บเดียว  
  expected ['sidewalk'] → top5 ['crosswalk_no_stop', 'wrong_way', 'hit_and_run', 'speeding', 'emergency_no_yield'] ✗ missing sidewalk
- **s06** [offense:hybrid] ขับมาเกือบร้อยหกสิบ ถนนเส้นนั้นเขาให้ร้อยยี่สิบ  
  expected ['speeding'] → top5 ['crosswalk_no_stop', 'no_seatbelt', 'impaired', 'speeding', 'wrong_way'] ✓
- **s07** [offense:hybrid] มีคนยืนรอข้ามตรงแถบขาวดำ แต่ผมไม่ชะลอ ขับผ่านไปเลย  
  expected ['crosswalk_no_stop'] → top5 ['crosswalk_no_stop', 'no_seatbelt', 'impaired', 'emergency_no_yield', 'red_light'] ✓
- **s08** [offense:hybrid] เฉี่ยวกระจกข้างรถคันอื่นแล้วตกใจ เลยรีบไปต่อไม่ได้จอด  
  expected ['hit_and_run'] → top5 ['emergency_no_yield', 'hit_and_run', 'wrong_way', 'no_plate', 'plate_incomplete'] ✓
- **s09** [offense:hybrid] นั่งหลังพวงมาลัยทั้งที่ไม่ได้รัดอะไรเลย  
  expected ['no_seatbelt'] → top5 ['no_seatbelt', 'phone', 'sidewalk', 'no_plate', 'no_helmet_passenger'] ✓
- **s10** [offense:hybrid] ทะเบียนหลุดหายไปตั้งแต่อาทิตย์ก่อน ยังขับใช้ปกติ  
  expected ['no_plate'] → top5 ['plate_incomplete', 'no_plate', 'no_seatbelt', 'impaired', 'plate_altered'] ✓
- **s11** [offense:hybrid] ลูกสามขวบนั่งตักแม่ที่เบาะหน้า ไม่มีคาร์ซีท ผมขับเองก็ไม่ได้คาด  
  expected ['no_seatbelt'] → top5 ['no_seatbelt', 'sidewalk', 'phone', 'no_helmet_passenger', 'no_helmet'] ✓
- **s12** [offense:hybrid] ขี่มอไซค์ซ้อนแฟนไปกินข้าว ทั้งคู่ไม่มีหมวก  
  expected ['no_helmet', 'no_helmet_passenger'] → top5 ['no_helmet', 'no_helmet_passenger', 'hit_and_run', 'phone', 'no_seatbelt'] ✓
- **s13** [offense:hybrid] กินเบียร์มาสามกระป๋อง ขับกลับไวๆ ประมาณ 140 ในเมือง  
  expected ['drunk', 'speeding'] → top5 ['drunk', 'speeding', 'abnormal_driving', 'unpaid_ticket', 'suspended_license'] ✓
- **s14** [offense:hybrid] เลี้ยวเข้าซอยวันเวย์แบบทวนทาง แล้วคุยไลน์ไปด้วย  
  expected ['phone', 'wrong_way'] → top5 ['wrong_way', 'abnormal_driving', 'crosswalk_no_stop', 'phone', 'hit_and_run'] ✓
- **s15** [offense:hybrid] โดนตำรวจเรียกตรวจ เป่าแล้วเกิน แถมไม่ได้คาดเข็มขัด  
  expected ['drunk', 'no_seatbelt'] → top5 ['no_seatbelt', 'unpaid_ticket', 'hit_and_run', 'speeding', 'no_regard_safety'] ✗ missing drunk
- **s16** [offense:hybrid] ทำงานสองกะติดกันจนหลับใน ไปชนเสาไฟข้างทาง แล้วก็ขับต่อไปเลยไม่ได้แจ้งใคร  
  expected ['hit_and_run', 'impaired'] → top5 ['hit_and_run', 'no_seatbelt', 'red_light', 'abnormal_driving', 'no_regard_safety'] ✗ missing impaired
- **s17** [offense:hybrid] รถพยาบาลเปิดไฟมาข้างหลังแต่ไม่หลบ แถมฝ่าแดงหนีไปอีก  
  expected ['emergency_no_yield', 'red_light'] → top5 ['emergency_no_yield', 'hit_and_run', 'red_light', 'crosswalk_no_stop', 'reckless'] ✓
- **s18** [offense:hybrid] ขี่มอไซค์ไม่ใส่หมวกขึ้นฟุตปาธ ขับปาดซ้ายปาดขวา  
  expected ['no_helmet', 'reckless', 'sidewalk'] → top5 ['no_helmet', 'no_helmet_passenger', 'sidewalk', 'hit_and_run', 'reckless'] ✓
- **s19** [offense:hybrid] เสพยามาแล้วรวมแก๊งแข่งรถบนถนนเลียบทางด่วนตอนตีสาม  
  expected ['drugs', 'street_racing'] → top5 ['drugs', 'street_racing', 'wrong_way', 'drunk', 'suspended_license'] ✓
- **s20** [offense:hybrid] ขับรถส่ายไปมาเบียดคันอื่น เพราะมัวแต่ก้มดูมือถือ  
  expected ['phone', 'reckless'] → top5 ['abnormal_driving', 'reckless', 'phone', 'no_regard_safety', 'wrong_way'] ✓
