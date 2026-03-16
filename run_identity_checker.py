# run_identity_checker.py
# Удобный запуск системы идентификации VK

import os
import sys

from identity_checker import IdentityChecker


def print_header():
    """Выводит заголовок программы"""
    print("\n" + "="*60)
    print("🔍 СИСТЕМА ИДЕНТИФИКАЦИИ ПРОФИЛЕЙ VK")
    print("   Комплексный анализ для определения совпадения")
    print("="*60)


def print_menu():
    """Выводит меню"""
    print("\n📋 МЕНЮ:")
    print("  1. Сравнить два профиля по URL")
    print("  2. Сравнить профиль из папки с профилем по URL")
    print("  3. Сравнить два профиля из папок")
    print("  4. Выход")


def get_profile_input(prompt_num):
    """Запрашивает ввод профиля"""
    print(f"\nВведите URL или ID профиля {prompt_num}:")
    print("  Примеры: vk.com/id123456789, id123456789, dariapalchik")
    return input("  > ").strip()


def get_folder_input(prompt_num):
    """Запрашивает ввод пути к папке"""
    print(f"\nВведите путь к папке с профилем {prompt_num}:")
    print("  Пример: vk_results/dariapalchik_20260302_130051")
    path = input("  > ").strip()
    
    # Проверяем, существует ли папка
    if os.path.isdir(path):
        return path
    else:
        print(f"  ⚠️ Папка не найдена: {path}")
        return None


def main():
    """Главная функция"""
    print_header()
    
    # Проверяем наличие токена
    try:
        from config import VK_TOKEN
        if not VK_TOKEN or len(VK_TOKEN) < 20:
            print("\n⚠️ Внимание: Токен VK API не найден или слишком короткий.")
            print("   Для работы укажите токен в файле config.py")
            print("   Получить токен: https://vk.com/apps?act=manage")
            return
    except ImportError:
        print("\n⚠️ Вниматие: Файл config.py не найден")
        return
    
    checker = IdentityChecker()
    
    if not checker.api:
        print("\n❌ Не удалось инициализировать API клиент")
        return
    
    while True:
        print_menu()
        choice = input("\nВыберите пункт (1-4): ").strip()
        
        if choice == "1":
            # Оба профиля по URL
            profile1_url = get_profile_input(1)
            if not profile1_url:
                continue
            profile2_url = get_profile_input(2)
            if not profile2_url:
                continue
            
            # Загружаем профили
            p1 = checker.load_profile(profile1_url)
            if not p1:
                print("❌ Не удалось загрузить первый профиль")
                continue
                
            p2 = checker.load_profile(profile2_url)
            if not p2:
                print("❌ Не удалось загрузить второй профиль")
                continue
            
            # Сравниваем
            checker.compare_profiles(p1, p2)
            
            # Предлагаем сохранить
            save = input("\nСохранить результаты? (д/н): ").strip().lower()
            if save == "д" or save == "y":
                output_file = input("Введите имя файла (или Enter для auto): ").strip()
                if not output_file:
                    output_file = f"comparison_{p1['profile'].get('id', 'p1')}_{p2['profile'].get('id', 'p2')}.json"
                checker.save_results(
                    checker.compare_profiles(p1, p2),
                    output_file
                )
        
        elif choice == "2":
            # Профиль из папки + URL
            folder = get_folder_input(1)
            if not folder:
                continue
            profile_url = get_profile_input(2)
            if not profile_url:
                continue
            
            # Загружаем профили
            p1 = checker.load_from_file(folder)
            if not p1:
                print("❌ Не удалось загрузить профиль из папки")
                continue
                
            p2 = checker.load_profile(profile_url)
            if not p2:
                print("❌ Не удалось загрузить профиль")
                continue
            
            # Сравниваем
            checker.compare_profiles(p1, p2)
        
        elif choice == "3":
            # Оба из папок
            folder1 = get_folder_input(1)
            if not folder1:
                continue
            folder2 = get_folder_input(2)
            if not folder2:
                continue
            
            # Загружаем профили
            p1 = checker.load_from_file(folder1)
            if not p1:
                print("❌ Не удалось загрузить первый профиль")
                continue
                
            p2 = checker.load_from_file(folder2)
            if not p2:
                print("❌ Не удалось загрузить второй профиль")
                continue
            
            # Сравниваем
            checker.compare_profiles(p1, p2)
            
            # Предлагаем сохранить
            save = input("\nСохранить результаты? (д/н): ").strip().lower()
            if save == "д" or save == "y":
                output_file = input("Введите имя файла: ").strip()
                if output_file:
                    p1_id = p1.get('profile', {}).get('id', 'p1')
                    p2_id = p2.get('profile', {}).get('id', 'p2')
                    result = checker.compare_profiles(p1, p2)
                    checker.save_results(result, output_file)
        
        elif choice == "4":
            print("\n👋 До свидания!")
            break
        
        else:
            print("\n⚠️ Неверный выбор. Попробуйте снова.")
        
        input("\nНажмите Enter для продолжения...")


if __name__ == "__main__":
    main()
