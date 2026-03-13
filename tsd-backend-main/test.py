import calendar
from datetime import datetime
from collections import defaultdict
import random
from tabulate import tabulate
import csv


class ScheduleGenerator:
    def __init__(self, groups, start_date=None):
        self.groups = groups
        self.start_date = start_date or datetime.now().replace(day=1)
        self.work_hours = defaultdict(int)
        self.schedule = defaultdict(dict)
        self.assigned_today = defaultdict(set)
        self.person_work_days_count = defaultdict(int)
        self.person_week_patterns = defaultdict(list)

        self.target_work_days = 22

        self.week_patterns = [
            [1, 1, 1, 1, 1, 0, 0],

            [1, 1, 1, 1, 0, 1, 0],

            [1, 1, 1, 0, 1, 0, 1]
        ]

        self.group_shift_mapping = {
            0: {
                'group_A': ['08:00-17:00', '09:00-18:00', '13:00-22:00'],
                'group_B': ['10:00-19:00', '11:00-20:00', '12:00-21:00']
            },
            1: {
                'group_A': ['10:00-19:00', '11:00-20:00', '12:00-21:00'],
                'group_B': ['08:00-17:00', '09:00-18:00', '13:00-22:00']
            }
        }

        self.workday_shifts = {
            '08:00-17:00': 2,
            '09:00-18:00': 2,
            '10:00-19:00': 2,
            '11:00-20:00': 3,
            '12:00-21:00': 3,
            '13:00-22:00': 2
        }

        self.weekend_shifts = {
            '08:00-17:00': 1,
            '10:00-19:00': 1,
            '13:00-22:00': 1
        }

    def generate_monthly_schedule(self):
        """Генерация расписания на месяц по недельным шаблонам"""
        year = self.start_date.year
        month = self.start_date.month

        month_days = self._get_month_days(year, month)
        weeks = self._split_into_weeks(month_days)

        print(f"Генерация расписания на {len(month_days)} дней...")
        print(f"Количество недель: {len(weeks)}")
        print(f"Цель: {self.target_work_days} рабочих дней на сотрудника")

        print("\n1. Выбор недельных шаблонов для сотрудников...")
        self._assign_week_patterns(weeks)

        print("2. Назначение рабочих дней по шаблонам...")
        self._assign_work_days_by_patterns(weeks)

        print("3. Заполнение смен с ротацией групп...")
        self._fill_all_shifts_with_rotation(weeks)

        return dict(self.schedule), dict(self.work_hours)

    def _get_month_days(self, year, month):
        """Получаем все дни месяца"""
        _, num_days = calendar.monthrange(year, month)
        return [datetime(year, month, day) for day in range(1, num_days + 1)]

    def _split_into_weeks(self, days):
        """Разделяем дни на недели"""
        weeks = []
        current_week = []

        for day in days:
            current_week.append(day)
            if day.weekday() == 6:
                weeks.append(current_week)
                current_week = []

        if current_week:
            weeks.append(current_week)

        return weeks

    def _get_all_people(self):
        """Получаем всех сотрудников"""
        all_people = []
        for group_people in self.groups.values():
            all_people.extend(group_people)
        return list(set(all_people))

    def _get_person_group(self, person):
        """Определяет группу сотрудника"""
        if person in self.groups['group_A']:
            return 'group_A'
        elif person in self.groups['group_B']:
            return 'group_B'
        return None

    def _assign_week_patterns(self, weeks):
        """Выбирает недельные шаблоны для каждого сотрудника"""
        all_people = self._get_all_people()

        for person in all_people:
            total_work_days = 0
            patterns = []

            for week in weeks:
                pattern = random.choice(self.week_patterns)
                patterns.append(pattern)
                work_days_in_week = sum(pattern[:len(week)])
                total_work_days += work_days_in_week

            self.person_week_patterns[person] = patterns

            print(f"  {person}: {total_work_days} рабочих дней по шаблонам")

    def _assign_work_days_by_patterns(self, weeks):
        """Назначает рабочие дни согласно шаблонам"""
        all_people = self._get_all_people()

        for week_idx, week in enumerate(weeks):
            for day_idx, date in enumerate(week):
                if day_idx >= 7:
                    continue

                for person in all_people:
                    pattern = self.person_week_patterns[person][week_idx]
                    if day_idx < len(pattern) and pattern[day_idx] == 1:
                        self.assigned_today[date].add(person)
                        self.person_work_days_count[person] += 1

    def _assign_shift(self, date, shift_time, person):
        """Назначает смену сотруднику"""
        if date not in self.schedule:
            self.schedule[date] = {}
        if shift_time not in self.schedule[date]:
            self.schedule[date][shift_time] = []

        group = self._get_person_group(person)

        self.schedule[date][shift_time].append({
            'person': person,
            'group': group
        })

        self.work_hours[person] += 9

    def _fill_all_shifts_with_rotation(self, weeks):
        """Заполняет смены с учетом ротации групп по неделям"""
        all_people = self._get_all_people()

        for week_idx, week in enumerate(weeks):
            week_type = week_idx % 2
            shift_mapping = self.group_shift_mapping[week_type]

            for date in week:
                working_people = list(self.assigned_today[date])
                if not working_people:
                    continue

                if date.weekday() < 5:
                    self._assign_workday_shifts(date, working_people, shift_mapping)
                else:
                    self._assign_weekend_shifts(date, working_people)

    def _assign_workday_shifts(self, date, working_people, shift_mapping):
        """Распределяет смены в будний день с учетом ротации групп"""
        group_a_people = [p for p in working_people if p in self.groups['group_A']]
        group_b_people = [p for p in working_people if p in self.groups['group_B']]
        group_a_shifts = shift_mapping['group_A']
        group_b_shifts = shift_mapping['group_B']

        for i, person in enumerate(group_a_people):
            shift = group_a_shifts[i % len(group_a_shifts)]
            self._assign_shift(date, shift, person)

        for i, person in enumerate(group_b_people):
            shift = group_b_shifts[i % len(group_b_shifts)]
            self._assign_shift(date, shift, person)

    def _assign_weekend_shifts(self, date, working_people):
        """Распределяет смены в выходной день"""
        shifts = list(self.weekend_shifts.keys())
        for i, person in enumerate(working_people[:3]):
            shift = shifts[i % len(shifts)]
            self._assign_shift(date, shift, person)

    def export_to_csv(self, filename=None):
        """Экспорт расписания в CSV файл"""
        if filename is None:
            filename = f"schedule_{self.start_date.strftime('%Y_%m')}.csv"

        month_days = sorted(self.schedule.keys())
        all_people = self._get_all_people()

        csv_data = []

        header = ['Сотрудник']
        for date in month_days:
            header.append(date.strftime('%d.%m.%Y'))
        csv_data.append(header)

        days_row = ['']
        for date in month_days:
            days_row.append(date.strftime('%A'))
        csv_data.append(days_row)

        for person in all_people:
            person_row = [person]

            for date in month_days:
                shift_info = 'Выходной'
                if date in self.schedule:
                    for shift_time, people_list in self.schedule[date].items():
                        for info in people_list:
                            if info['person'] == person:
                                shift_info = f"{shift_time}"
                                break
                        if shift_info != 'Выходной':
                            break

                person_row.append(shift_info)

            csv_data.append(person_row)

        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile, delimiter=',')
            writer.writerows(csv_data)

        print(f"\n✅ Расписание экспортировано в файл: {filename}")
        return filename

    def print_table_schedule(self):
        """Вывод статистики расписания"""
        print("=" * 80)
        print(f"РАСПИСАНИЕ НА {self.start_date.strftime('%B %Y')}")
        print("=" * 80)
        print("\nСТАТИСТИКА ПО СОТРУДНИКАМ:")
        print("-" * 50)

        stats_data = []
        all_people = self._get_all_people()

        for person in sorted(all_people):
            work_days = self.person_work_days_count[person]
            hours = self.work_hours[person]
            weekend_works = sum(1 for date in self.schedule
                                if date.weekday() >= 5 and
                                any(info['person'] == person
                                    for shift in self.schedule[date].values()
                                    for info in shift))
            stats_data.append([person, work_days, weekend_works, hours])

        print(tabulate(stats_data,
                       headers=['Сотрудник', 'Рабочих дней', 'Выходных смен', 'Часов'],
                       tablefmt='grid'))
        print("=" * 80)

    def validate_schedule(self):
        """Проверяет соответствие расписания требованиям"""
        print("\nПРОВЕРКА РАСПИСАНИЯ:")
        print("-" * 30)

        all_valid = True
        all_people = self._get_all_people()

        for person in all_people:
            days_count = self.person_work_days_count[person]
            if days_count != self.target_work_days:
                print(f"❌ {person}: {days_count} рабочих дней (должно быть {self.target_work_days})")
                all_valid = False
            else:
                print(f"✅ {person}: {days_count} рабочих дней")

        weekends = [day for day in self.schedule.keys() if day.weekday() >= 5]
        for date in weekends:
            workers_count = len(self.assigned_today[date])
            if workers_count > 3:
                print(f"❌ {date.strftime('%d.%m')}: {workers_count} человек в выходной (максимум 3)")
                all_valid = False

        weeks = self._split_into_weeks(sorted(self.schedule.keys()))
        for week_idx, week in enumerate(weeks):
            week_type = week_idx % 2
            shift_mapping = self.group_shift_mapping[week_type]

            for date in week:
                if date.weekday() < 5:
                    for shift_time, people_list in self.schedule[date].items():
                        for info in people_list:
                            group = info['group']
                            expected_shifts = shift_mapping[group]
                            if shift_time not in expected_shifts:
                                print(f"❌ Неправильная смена {shift_time} для {info['person']} в неделю {week_idx + 1}")
                                all_valid = False

        if all_valid:
            print("\n✅ Все проверки пройдены успешно!")

        return all_valid


if __name__ == "__main__":
    groups = {
        'group_A': ['AChernenko', 'VGlebov', 'MShepelin', 'PChmil', 'IKornilov', 'AMysin', 'FPribytkov', 'EShults',
                    'KKorsakova', 'ELyulenov','DBurak','SShilkov'],
        'group_B': ['AVikulov', 'EFursova', 'ALapshov', 'VDomrachev', 'LKhoderian', 'MYakovlev', 'AKuzmin',
                    'DPleshakov', 'APulnikov', 'IFillipov','NSavin','AMoskaleva']
    }

    generator = ScheduleGenerator(groups, datetime(2024, 8, 1))

    try:
        schedule, work_hours = generator.generate_monthly_schedule()
        generator.print_table_schedule()
        generator.validate_schedule()
        generator.export_to_csv()

    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback

        traceback.print_exc()