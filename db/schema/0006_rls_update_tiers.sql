-- Update posts insert policy to require premium for private posts

drop policy if exists "posts insert member author" on posts;

create policy "posts insert member author" on posts for insert
  with check (
    user_id = auth.uid()
    and exists (
      select 1 from user_programs up
      where up.user_id = auth.uid()
        and up.program_id = posts.program_id
        and (
          posts.visibility = 'public' or up.tier = 'premium'
        )
    )
  );

