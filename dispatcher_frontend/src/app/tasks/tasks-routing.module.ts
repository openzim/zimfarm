import { NgModule }            from '@angular/core';
import { RouterModule }        from '@angular/router';

import { TasksComponent }    from './tasks.component';

@NgModule({
  imports: [RouterModule.forChild([
    { path: '', component: TasksComponent }
  ])],
  exports: [RouterModule]
})
export class TasksRoutingModule {}