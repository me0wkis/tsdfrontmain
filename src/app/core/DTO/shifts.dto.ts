// GET shift-types
export interface ShiftTypesDTO extends ShiftTypeRequestDTO {
  id: number;
}

// POST shift-types
export interface ShiftTypeRequestDTO {
  name: string;
  code: string;
  is_work_shift: boolean;
}

// GET shift-templates
export interface ShiftTemplatesDTO extends ShiftTemplateRequestDTO {
  id: number;
}

//POST shift-templates
export interface ShiftTemplateRequestDTO {
  code: string;
  description: string;
  is_fixed_time: boolean;
  start_time: string;
  end_time: string;
  lunch_start_time: string;
  lunch_end_time: string;
  shift_type: number;
  icon: string;
  allowed_roles: string;
  is_active: boolean;
  is_office: boolean;
}

// GET shifts
export interface ShiftsDTO {
  count: number;
  next: string | null;
  previous: string | null;
  results: ShiftDTO[];
}

export interface ShiftDTO {
  id: number;
  user: string;
  shift_date: string;
  job_title: string;
  shift_type: string;
  start_time: string;
  end_time: string;
  lunch_start_time: string;
  lunch_end_time: string;
  work_hours: string;
  shift_template: string;
  created_by: string;
  is_fixed_time: boolean;
}

// POST shifts
export interface ShiftRequestDTO {
  user: string;
  shift_date: string;
  job_title: string;
  shift_type: string;
  start_time: string;
  end_time: string;
  lunch_start_time: string;
  lunch_end_time: string;
  shift_template: string;
  created_by: string;
}
