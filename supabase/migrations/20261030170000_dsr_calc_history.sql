-- DSR 계산기 기록 (daeguprn 프로젝트에 적용됨)
-- 로그인 없이 브라우저별 랜덤 device_id(localStorage)로 구분, 기기당 최신 10개 유지
create table public.dsr_calc_history (
  id bigint generated always as identity primary key,
  device_id uuid not null,
  created_at timestamptz not null default now(),
  inputs jsonb not null check (pg_column_size(inputs) <= 8192),
  dsr numeric(6,2) not null,
  dti numeric(6,2) not null,
  status text not null check (status in ('ok','warn','no'))
);
create index dsr_calc_history_device_idx on public.dsr_calc_history (device_id, created_at desc);

-- 직접 접근 차단: RLS on, 정책 없음 → 아래 RPC로만 접근
alter table public.dsr_calc_history enable row level security;
revoke all on public.dsr_calc_history from anon, authenticated;

-- 저장 + 기기별 최신 10개만 유지
create or replace function public.dsr_history_save(p_device uuid, p_inputs jsonb, p_dsr numeric, p_dti numeric, p_status text)
returns bigint language plpgsql security definer set search_path = public as $$
declare new_id bigint;
begin
  insert into dsr_calc_history (device_id, inputs, dsr, dti, status)
  values (p_device, p_inputs, p_dsr, p_dti, p_status) returning id into new_id;
  delete from dsr_calc_history
   where device_id = p_device
     and id not in (select id from dsr_calc_history where device_id = p_device order by created_at desc, id desc limit 10);
  return new_id;
end $$;

create or replace function public.dsr_history_list(p_device uuid)
returns table (id bigint, created_at timestamptz, inputs jsonb, dsr numeric, dti numeric, status text)
language sql stable security definer set search_path = public as $$
  select id, created_at, inputs, dsr, dti, status from dsr_calc_history
   where device_id = p_device order by created_at desc, id desc limit 10;
$$;

create or replace function public.dsr_history_delete(p_device uuid, p_id bigint)
returns void language sql security definer set search_path = public as $$
  delete from dsr_calc_history where device_id = p_device and id = p_id;
$$;

revoke all on function public.dsr_history_save(uuid,jsonb,numeric,numeric,text) from public;
revoke all on function public.dsr_history_list(uuid) from public;
revoke all on function public.dsr_history_delete(uuid,bigint) from public;
grant execute on function public.dsr_history_save(uuid,jsonb,numeric,numeric,text) to anon, authenticated;
grant execute on function public.dsr_history_list(uuid) to anon, authenticated;
grant execute on function public.dsr_history_delete(uuid,bigint) to anon, authenticated;
