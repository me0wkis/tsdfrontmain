import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { ScheduleRoutingModule } from './schedule-routing-module';
import { SchedulePage } from './pages/schedule-page/schedule-page';

@NgModule({
  declarations: [],
  imports: [
    CommonModule,
    ScheduleRoutingModule,
    SchedulePage
  ]
})
export class ScheduleModule {}
