import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { SchedulePage } from './pages/schedule-page/schedule-page';

const routes: Routes = [
  {
    path: '',
    redirectTo: getCurrentYearMonth(), // функция для получения текущих года и месяца
    pathMatch: 'full'
  },
  {
    path: ':year/:month',
    component: SchedulePage
  }
];

// getCurrentYearMonth — функция, возвращающая строку вида '2024/7'
function getCurrentYearMonth(): string {
  const today = new Date();
  return `${today.getFullYear()}/${today.getMonth() + 1}`;
}

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule]
})
export class ScheduleRoutingModule { }
