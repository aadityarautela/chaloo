import { Routes } from '@angular/router';
import { PlannerPageComponent } from './pages/planner';

export const routes: Routes = [
  { path: '', component: PlannerPageComponent },
  { path: '**', redirectTo: '' }
];
