// DTO imports
import {
  ShiftsDTO,
  ShiftDTO,
  ShiftRequestDTO,
  ShiftTypesDTO,
  ShiftTypeRequestDTO,
  ShiftTemplatesDTO,
  ShiftTemplateRequestDTO,
} from '@/core/DTO/shifts.dto';
import {
  UsersResponsePaginatedDTO,
  UserDTO,
  UserRequestDTO,
} from '@/core/DTO/users.dto';
import {
  ScheduleResponseDTO,
  TeamNameDTO,
  UserScheduleDTO,
  UserShiftsDTO,
} from '@/core/DTO/schedule.dto';
import {
  CalendarAnomalyDTO,
  AnomaliesResponseDTO,
} from '@/core/DTO/anomalies.dto';
import { TeamDto } from '@/core/DTO/teams.dto';
import { DeskDTO } from '@/core/DTO/desks.dto';

// Model imports
import {
  Shifts,
  ShiftsResponse,
  ShiftRequest,
  ShiftTypes,
  ShiftTypeRequest,
  ShiftTemplates,
  ShiftTemplateRequest,
} from '@shared/models/shifts.model';
import { UsersResponse, User, UserRequest } from '@shared/models/users.model';
import {
  ScheduleResponse,
  TeamName,
  UserSchedule,
  Shift,
} from '@shared/models/schedule.model';
import {
  CalendarAnomaly,
  AnomaliesResponse,
} from '@shared/models/anomalies.model';
import { Team } from '@shared/models/teams.model';
import { Desk } from '@shared/models/desks.model';

export class MapperUtil {
  // Users mapping
  static usersResponseFromDto(dto: UsersResponsePaginatedDTO): UsersResponse {
    return {
      count: dto.count,
      next: dto.next,
      previous: dto.previous,
      results: dto.results.map((user: UserDTO) => this.userFromDto(user)),
    };
  }

  static userFromDto(dto: UserDTO): User {
    return {
      id: dto?.id || 0,
      alias: dto?.alias || '',
      firstName: dto?.first_name || '',
      secondName: dto?.second_name || '',
      jobTitle: dto?.job_title || '',
      groupName: dto?.group_name || '',
      hiringDate: dto?.hiring_date || '',
      supervisorName: dto?.supervisor_name || '',
      email: dto?.email || '',
      phoneNumber: dto?.phone_number || '',
      desk: dto?.desk || 0,
      team: dto?.team || 0,
      avatarUrl: dto?.avatar_url || null,
      isActive: dto?.is_active === 1,
    };
  }

  static userToRequestDto(model: UserRequest): UserRequestDTO {
    return {
      alias: model.alias,
      first_name: model.firstName,
      second_name: model.secondName,
      job_title: model.jobTitle,
      group_name: model.groupName,
      hiring_date: model.hiringDate,
      supervisor_name: model.supervisorName,
      email: model.email,
      phone_number: model.phoneNumber,
      desk: model.desk,
      team: model.team,
      avatar_url: model.avatarUrl,
      is_active: model.isActive ? 1 : 0,
    };
  }

  // Shifts mapping
  static shiftsResponseFromDto(dto: ShiftsDTO): ShiftsResponse {
    return {
      count: dto.count,
      next: dto.next,
      previous: dto.previous,
      results: dto.results.map((shift: ShiftDTO) => this.shiftFromDto(shift)),
    };
  }

  static shiftFromDto(dto: ShiftDTO): Shifts {
    return {
      id: dto.id,
      user: dto.user,
      shiftDate: dto.shift_date,
      jobTitle: dto.job_title,
      shiftType: dto.shift_type,
      startTime: dto.start_time,
      endTime: dto.end_time,
      lunchStartTime: dto.lunch_start_time,
      lunchEndTime: dto.lunch_end_time,
      workHours: dto.work_hours,
      shiftTemplate: dto.shift_template,
      createdBy: dto.created_by,
      isFixedTime: dto.is_fixed_time,
    };
  }

  static shiftToRequestDto(model: ShiftRequest): ShiftRequestDTO {
    return {
      user: model.user,
      shift_date: model.shiftDate,
      job_title: model.jobTitle,
      shift_type: model.shiftType,
      start_time: model.startTime,
      end_time: model.endTime,
      lunch_start_time: model.lunchStartTime,
      lunch_end_time: model.lunchEndTime,
      shift_template: model.shiftTemplate,
      created_by: model.createdBy,
    };
  }

  // ShiftTypes mapping
  static shiftTypeFromDto(dto: ShiftTypesDTO): ShiftTypes {
    return {
      id: dto.id,
      name: dto.name,
      code: dto.code,
      isWorkShift: dto.is_work_shift,
    };
  }

  static shiftTypeToRequestDto(model: ShiftTypeRequest): ShiftTypeRequestDTO {
    return {
      name: model.name,
      code: model.code,
      is_work_shift: model.isWorkShift,
    };
  }

  // ShiftTemplates mapping
  static shiftTemplateFromDto(dto: ShiftTemplatesDTO): ShiftTemplates {
    return {
      id: dto.id,
      code: dto.code,
      description: dto.description,
      isFixedTime: dto.is_fixed_time,
      startTime: dto.start_time,
      endTime: dto.end_time,
      lunchStartTime: dto.lunch_start_time,
      lunchEndTime: dto.lunch_end_time,
      shiftType: dto.shift_type,
      icon: dto.icon,
      allowedRoles: dto.allowed_roles,
      isActive: dto.is_active,
      isOffice: dto.is_office,
    };
  }

  static shiftTemplateToRequestDto(
    model: ShiftTemplateRequest
  ): ShiftTemplateRequestDTO {
    return {
      code: model.code,
      description: model.description,
      is_fixed_time: model.isFixedTime,
      start_time: model.startTime,
      end_time: model.endTime,
      lunch_start_time: model.lunchStartTime,
      lunch_end_time: model.lunchEndTime,
      shift_type: model.shiftType,
      icon: model.icon,
      allowed_roles: model.allowedRoles,
      is_active: model.isActive,
      is_office: model.isOffice,
    };
  }

  // Schedule mapping
  static scheduleFromDto(dto: ScheduleResponseDTO): ScheduleResponse {
    return {
      year: dto?.year || 0,
      month: dto?.month || 0,
      monthName: dto?.month_name || '',
      teams: dto?.schedule
        ? dto.schedule.map((team: TeamNameDTO) =>
            this.teamScheduleFromDto(team)
          )
        : [],
    };
  }

  static teamScheduleFromDto(dto: TeamNameDTO): TeamName {
    return {
      teamName: dto?.team_name || '',
      users: dto?.users
        ? dto.users.map((user: UserScheduleDTO) =>
            this.userScheduleFromDto(user)
          )
        : [],
    };
  }

  static userScheduleFromDto(dto: UserScheduleDTO): UserSchedule {
    return {
      id: dto?.id || 0,
      fullName: dto?.full_name || '',
      shifts: dto?.shifts
        ? dto.shifts.map((shift: UserShiftsDTO) => this.userShiftFromDto(shift))
        : [],
    };
  }

  static userShiftFromDto(dto: UserShiftsDTO): Shift {
    return {
      id: dto?.id || 0,
      shiftDate: dto?.shift_date || '',
      jobTitle: dto?.job_title || null,
      shortCode: dto?.short_code || '',
      startTime: dto?.start_time || '',
      endTime: dto?.end_time || '',
      lunchStartTime: dto?.lunch_start_time || '',
      lunchEndTime: dto?.lunch_end_time || '',
      workHours: parseFloat(dto?.work_hours || '0'),
    };
  }

  // Calendar Anomalies mapping
  static calendarAnomalyFromDto(dto: CalendarAnomalyDTO): CalendarAnomaly {
    return {
      id: dto?.id || 0,
      date: dto?.date || '',
      name: dto?.name || '',
      type: dto?.type || '',
    };
  }

  static anomaliesResponseFromDto(
    dto: AnomaliesResponseDTO
  ): AnomaliesResponse {
    return {
      year: dto?.year || 0,
      month: dto?.month || 0,
      anomalies: dto?.anomalies
        ? dto.anomalies.map((anomaly: CalendarAnomalyDTO) =>
            this.calendarAnomalyFromDto(anomaly)
          )
        : [],
    };
  }

  // Teams mapping
  static teamFromDto(dto: TeamDto): Team {
    return {
      id: dto.id,
      name: dto.name,
      description: dto.description,
    };
  }

  // Desks mapping
  static deskFromDto(dto: DeskDTO): Desk {
    return {
      id: dto.id,
      deskNumber: dto.desk_number,
    };
  }
}
