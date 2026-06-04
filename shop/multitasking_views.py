"""
Дополнительное задание — многозадачность (Вариант 24 Кондитерская)
Threading:      продажа билетов на мастер-класс с threading.Lock
Multiprocessing: расчёт SHA-256 контрольных сумм партий через ProcessPoolExecutor
Asyncio:         параллельная валидация QR-кодов заказов через asyncio.gather
"""
import asyncio, hashlib, threading, time, random
from concurrent.futures import ProcessPoolExecutor
from django.shortcuts import render


# ═══════════════════ A: Threading — продажа мест на мастер-класс ═════════════

class Workshop:
    """Мастер-класс с ограниченным количеством мест."""
    def __init__(self, total=20):
        self.total = total
        self.sold = 0
        self.log = []
        self._lock = threading.Lock()

    def buy(self, client_id, qty):
        with self._lock:
            if self.sold + qty <= self.total:
                time.sleep(0.01)
                self.sold += qty
                self.log.append(f'✅ Клиент #{client_id} купил {qty} место(а). Занято: {self.sold}/{self.total}')
                return True
            else:
                self.log.append(f'❌ Клиент #{client_id} — нет мест (хотел {qty}, осталось {self.total - self.sold})')
                return False


def run_threading_demo():
    workshop = Workshop(total=20)
    threads = []
    clients = [(i, random.randint(1, 4)) for i in range(1, 12)]
    for cid, qty in clients:
        t = threading.Thread(target=workshop.buy, args=(cid, qty))
        threads.append(t)
    for t in threads: t.start()
    for t in threads: t.join()
    return {
        'log': workshop.log,
        'sold': workshop.sold,
        'total': workshop.total,
        'remaining': workshop.total - workshop.sold,
    }


# ═══════════════════ B: Multiprocessing — расчёт SHA-256 партий ══════════════

def hash_batch(batch_data):
    """Вычисляет SHA-256 для каждой позиции партии (CPU-задача)."""
    results = []
    for item in batch_data:
        raw = f'{item["order_id"]}-{item["product"]}-{item["qty"]}'.encode()
        digest = hashlib.sha256(raw).hexdigest()
        results.append({'label': f'Заказ #{item["order_id"]} / {item["product"]}',
                        'hash': digest[:16] + '…'})
    return results


def run_multiprocessing_demo():
    orders = [
        {'order_id': i, 'product': random.choice(['Наполеон','Медовик','Эклеры','Трюфели','Зефир']),
         'qty': random.randint(1,5)}
        for i in range(1, 41)
    ]
    # Разбиваем на 4 партии
    batch_size = len(orders) // 4
    batches = [orders[i:i+batch_size] for i in range(0, len(orders), batch_size)]

    start = time.time()
    with ProcessPoolExecutor(max_workers=4) as pool:
        results_nested = list(pool.map(hash_batch, batches))
    elapsed = time.time() - start

    results = [item for batch in results_nested for item in batch]
    return {'results': results, 'count': len(results), 'elapsed': round(elapsed, 3)}


# ═══════════════════ C: Asyncio — валидация QR-кодов заказов ════════════════

async def validate_qr(order_id):
    """Имитирует асинхронную проверку QR-кода через внешний сервис."""
    await asyncio.sleep(random.uniform(0.05, 0.15))
    valid = order_id % 7 != 0  # каждый 7-й невалидный (для демонстрации)
    return {
        'order_id': order_id,
        'qr_code': f'QR-{order_id:04d}-{hashlib.md5(str(order_id).encode()).hexdigest()[:6].upper()}',
        'valid': valid,
        'status': '✅ Действителен' if valid else '❌ Недействителен',
    }


async def validate_all_qr(order_ids):
    tasks = [validate_qr(oid) for oid in order_ids]
    return await asyncio.gather(*tasks)


def run_asyncio_demo():
    order_ids = list(range(1, 21))
    start = time.time()
    results = asyncio.run(validate_all_qr(order_ids))
    elapsed = time.time() - start
    valid_count = sum(1 for r in results if r['valid'])
    return {
        'results': list(results),
        'total': len(results),
        'valid': valid_count,
        'invalid': len(results) - valid_count,
        'elapsed': round(elapsed, 3),
    }


# ═══════════════════ View ════════════════════════════════════════════════════

def multitasking(request):
    run = request.GET.get('run', '')
    context = {'run': run}

    if run in ('a', 'all'):
        context['threading_result'] = run_threading_demo()
    if run in ('b', 'all'):
        context['mp_result'] = run_multiprocessing_demo()
    if run in ('c', 'all'):
        context['asyncio_result'] = run_asyncio_demo()

    return render(request, 'multitasking.html', context)
