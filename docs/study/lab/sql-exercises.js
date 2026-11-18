/* Original synthetic practice data; SQLite dialect. Also used by the worker. */
(function(root){
var setup="CREATE TABLE customers(id INTEGER PRIMARY KEY,name TEXT,region TEXT); CREATE TABLE orders(id INTEGER PRIMARY KEY,customer_id INTEGER,amount INTEGER,status TEXT); INSERT INTO customers VALUES(1,'민지','서울'),(2,'준호','부산'),(3,'수빈','서울'),(4,'지우',NULL); INSERT INTO orders VALUES(1,1,100,'paid'),(2,1,50,'paid'),(3,2,200,'paid'),(4,3,80,'cancelled'),(5,2,50,'paid');";
var extra="INSERT INTO customers VALUES(5,'하린','부산'),(6,'민지','서울'); INSERT INTO orders VALUES(6,5,150,'paid'),(7,6,150,'paid'),(8,4,0,'paid'),(9,5,100,'cancelled');";
var exercises=[
 ['filter','조건 조회','결제 완료(paid)이며 금액이 100 이상인 주문의 id, amount를 id 오름차순으로 조회하세요.','SELECT id, amount FROM orders WHERE status = \'paid\' AND amount >= 100 ORDER BY id',true,'WHERE에서 두 조건을 AND로 연결하세요.'],
 ['group','고객별 집계','결제 완료 주문을 고객별로 합산하세요. customer_id, total 열을 반환합니다.','SELECT customer_id, SUM(amount) AS total FROM orders WHERE status=\'paid\' GROUP BY customer_id',false,'취소 주문은 집계 전에 제외합니다.'],
 ['join','고객과 주문 연결','결제 완료 주문별 주문 번호 order_id와 고객 이름 name을 조회하세요.','SELECT o.id AS order_id,c.name FROM orders o JOIN customers c ON c.id=o.customer_id WHERE o.status=\'paid\'',false,'customers.id와 orders.customer_id가 연결됩니다.'],
 ['missing','주문 없는 고객','주문 자체가 한 건도 없는 고객의 id, name을 조회하세요. 취소 주문도 주문으로 봅니다.','SELECT c.id,c.name FROM customers c LEFT JOIN orders o ON o.customer_id=c.id WHERE o.id IS NULL',false,'LEFT JOIN 후 오른쪽 테이블의 기본 키가 NULL인지 확인하세요.'],
 ['having','집계 후 필터','결제 완료 합계가 150 이상인 customer_id, total을 조회하세요.','SELECT customer_id,SUM(amount) AS total FROM orders WHERE status=\'paid\' GROUP BY customer_id HAVING SUM(amount)>=150',false,'집계 결과 조건은 HAVING에 둡니다.'],
 ['null','NULL 처리','모든 고객의 id, region을 반환하되 지역 NULL은 미입력으로 바꾸세요.','SELECT id,COALESCE(region,\'미입력\') AS region FROM customers',false,'NULL = NULL 비교 대신 COALESCE를 활용하세요.'],
 ['rank','윈도 함수·동점','결제 완료 주문을 금액 내림차순 DENSE_RANK로 순위 매기세요. id, amount, amount_rank를 반환합니다.','SELECT id,amount,DENSE_RANK() OVER(ORDER BY amount DESC) AS amount_rank FROM orders WHERE status=\'paid\'',false,'동일 금액은 같은 순위이며 다음 순위를 건너뛰지 않습니다.'],
 ['quality','0건 포함 집계','모든 고객의 id, name, paid_count를 조회하세요. 결제 완료 주문이 없어도 0건으로 포함합니다.','SELECT c.id,c.name,COUNT(o.id) AS paid_count FROM customers c LEFT JOIN orders o ON c.id=o.customer_id AND o.status=\'paid\' GROUP BY c.id,c.name',false,'오른쪽 테이블 필터를 WHERE에 두면 0건 고객이 빠질 수 있습니다. COUNT(*)와 COUNT(o.id)를 비교하세요.']
].map(function(x){return {id:x[0],title:x[1],prompt:x[2],answer:x[3],ordered:x[4],hint:x[5]}});
root.SQL_PRACTICE_DATA={setup:setup,extra:extra,exercises:exercises};
})(typeof self!=='undefined'?self:globalThis);
