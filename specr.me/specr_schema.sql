CREATE TABLE computers (
    urlid integer primary key not null,
	system_name varchar(100) not null,
	creator_name varchar(100) not null,
	creator_IP inet not null default '0.0.0.0',
	mobo text not null,
	cpu_name text not null,
	gpu_name text not null,
	mem_size smallint not null,
	hdds text not null,
	monitors text not null,
    os_ver text not null default 'unknown'
);
