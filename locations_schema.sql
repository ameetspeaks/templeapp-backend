-- Create locations table to track progress of temple fetching
create table public.locations (
  id uuid not null default gen_random_uuid (),
  city text not null,
  state text not null,
  status text not null default 'pending', -- pending, processing, completed
  temple_count int default 0,
  last_scanned_at timestamp with time zone,
  created_at timestamp with time zone default now(),
  constraint locations_pkey primary key (id),
  constraint locations_city_state_key unique (city, state)
);

-- Index for fast lookup of pending cities
create index IF not exists idx_locations_status on public.locations using btree (status);
