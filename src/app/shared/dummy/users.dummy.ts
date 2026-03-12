import { DUMMY_TEAMS, Team } from './teams.dummy';
import { Desk, DUMMY_DESKS } from './desks.dummy';

export interface User {
  id: number;
  jobTitle: string;
  userTeamId: Team;
  hiringDate: Date;
  userDeskId: Desk;
  phoneNumber: string;
  avatarUrl: string;
  alias: string;
  firstName: string;
  secondName: string;
  email: string;
  groupName: string; // Название
  supervisorName: string;
  isActive: boolean;
}

export const DUMMY_USERS: User[] = [
  {
    id: 1,
    jobTitle: 'Service Desk Analyst',
    userTeamId: DUMMY_TEAMS[0],
    hiringDate: new Date('2022-03-15'),
    userDeskId: DUMMY_DESKS[0],
    phoneNumber: '+1-555-1234',
    avatarUrl: 'https://randomuser.me/api/portraits/women/1.jpg',
    alias: 'alice',
    firstName: 'Alice',
    secondName: 'Johnson',
    email: 'alice.johnson@example.com',
    groupName: 'Global Service Desk',
    supervisorName: 'Bob Smith',
    isActive: true,
  },
  {
    id: 2,
    jobTitle: 'Service Desk Analyst',
    userTeamId: DUMMY_TEAMS[1],
    hiringDate: new Date('2021-07-01'),
    userDeskId: DUMMY_DESKS[1],
    phoneNumber: '+1-555-5678',
    avatarUrl: 'https://randomuser.me/api/portraits/men/2.jpg',
    alias: 'bob',
    firstName: 'Bob',
    secondName: 'Smith',
    email: 'bob.smith@example.com',
    groupName: 'API Team',
    supervisorName: 'Diana Prince',
    isActive: true,
  },
  {
    id: 3,
    jobTitle: 'Service Desk Analyst',
    userTeamId: DUMMY_TEAMS[0],
    hiringDate: new Date('2020-11-20'),
    userDeskId: DUMMY_DESKS[2],
    phoneNumber: '+1-555-8765',
    avatarUrl: 'https://randomuser.me/api/portraits/men/3.jpg',
    alias: 'charlie',
    firstName: 'Charlie',
    secondName: 'Downer',
    email: 'charlie.downer@example.com',
    groupName: 'QA Team',
    supervisorName: 'Alice Johnson',
    isActive: false,
  },
  {
    id: 4,
    jobTitle: 'Project Manager',
    userTeamId: DUMMY_TEAMS[2],
    hiringDate: new Date('2019-05-10'),
    userDeskId: DUMMY_DESKS[3],
    phoneNumber: '+1-555-4321',
    avatarUrl: 'https://randomuser.me/api/portraits/women/4.jpg',
    alias: 'diana',
    firstName: 'Diana',
    secondName: 'Prince',
    email: 'diana.prince@example.com',
    groupName: 'Management',
    supervisorName: 'Ethan Hunt',
    isActive: true,
  },
  {
    id: 5,
    jobTitle: 'DevOps Engineer',
    userTeamId: DUMMY_TEAMS[2],
    hiringDate: new Date('2023-01-05'),
    userDeskId: DUMMY_DESKS[4],
    phoneNumber: '+1-555-6789',
    avatarUrl: 'https://randomuser.me/api/portraits/men/5.jpg',
    alias: 'ethan',
    firstName: 'Ethan',
    secondName: 'Hunt',
    email: 'ethan.hunt@example.com',
    groupName: 'DevOps',
    supervisorName: 'Bob Smith',
    isActive: true,
  },
];
