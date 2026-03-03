import unittest
from typing import Generator

# 1. Итератор (__getitem__)

class FibonacciGetItem:
    """
    Класс, реализующий доступ к числам Фибоначчи через индекс.
    """

    def __init__(self, limit: int):
        """
        Инициализация.

        Ключевые аргументы:
        limit - Количество чисел для генерации.
        """
        self.limit: int = limit

    def __getitem__(self, idx: int) -> int:
        """
        Возвращает число Фибоначчи по индексу.
        
        Ключевые аргументы:
        idx - Индекс элемента.
        return - Число Фибоначчи.
        raises IndexError - Если индекс выходит за пределы limit.
        """
        
        if idx < 0 or idx >= self.limit:
            raise IndexError("Индекс выходит за пределы лимита")

        a, b = 0, 1
        for _ in range(idx):
            a, b = b, a + b
        return a


# 2. Итератор (__iter__, __next__)

class FibonacciIterator:
    """
    Класс-итератор для чисел Фибоначчи.
    Использует классические методы __iter__ и __next__.
    """

    def __init__(self, limit: int):
        """
        Инициализация.

        Ключевые аргументы:
        limit - Количество чисел, которые нужно вернуть.
        """
        self.limit: int = limit
        self.count: int = 0
        self.a: int = 0
        self.b: int = 1

    def __iter__(self) -> 'FibonacciIterator':
        """Возвращает сам итератор."""
        return self

    def __next__(self) -> int:
        """
        Возвращает следующее число Фибоначчи.
        
        return - Следующее число ряда.
        raises StopIteration - Когда достигнут лимит.
        """
        if self.count >= self.limit:
            raise StopIteration

        result = self.a
        self.a, self.b = self.b, self.a + self.b
        self.count += 1
        return result


# 3. Сопрограмма (Генератор)

def fibonacci_coroutine(limit: int) -> Generator[int, None, None]:
    """
    Генератор (сопрограмма), возвращающая числа ряда Фибоначчи.

    Ключевые аргументы:
    limit - Количество чисел для генерации.
    yield - Число Фибоначчи.
    """
    a, b = 0, 1
    for _ in range(limit):
        yield a
        a, b = b, a + b


# Тесты 

class TestFibonacciImplementations(unittest.TestCase):
    """Набор тестов для проверки всех реализаций."""

    # Ожидаемая последовательность для 10 чисел:
    EXPECTED = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
    LIMIT = 10

    def test_getitem_implementation(self):
        """Тест реализации через __getitem__."""
        fib_obj = FibonacciGetItem(self.LIMIT)
        
        # Проверка итерации
        result = list(fib_obj)
        self.assertEqual(result, self.EXPECTED)
        
        # Проверка прямого доступа
        self.assertEqual(fib_obj[5], 5)
        self.assertEqual(fib_obj[9], 34)
        
        # Проверка выхода за границы
        with self.assertRaises(IndexError):
            a = fib_obj[self.LIMIT]

    def test_iterator_implementation(self):
        """Тест классического итератора."""
        fib_iter = FibonacciIterator(self.LIMIT)
        
        # Проверка итерации
        result = list(fib_iter)
        self.assertEqual(result, self.EXPECTED)
        
        # Проверка повторного использования
        self.assertEqual(list(fib_iter), [])

    def test_coroutine_implementation(self):
        """Тест генератора/сопрограммы."""
        fib_gen = fibonacci_coroutine(self.LIMIT)
        
        # Проверка типа
        self.assertTrue(isinstance(fib_gen, Generator))
        
        # Проверка данных
        result = list(fib_gen)
        self.assertEqual(result, self.EXPECTED)

if __name__ == '__main__':
    unittest.main()