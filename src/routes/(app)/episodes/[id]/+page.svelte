<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';

	import { user } from '$lib/stores';
	import { getEpisodeById, updateEpisode, deleteEpisode } from '$lib/apis/episodes';

	let loaded = false;
	let episode = null;
	let isEditing = false;

	// 编辑表单
	let title = '';
	let question = '';
	let reasoning = '';
	let solution = '';
	let references = '';
	let status = 'draft';

	const loadEpisode = async () => {
		const id = $page.params.id;
		try {
			episode = await getEpisodeById(localStorage.token, id);
			if (episode) {
				title = episode.title || '';
				question = episode.question || '';
				reasoning = episode.reasoning || '';
				solution = episode.solution || '';
				references = (episode.references || []).join('\n');
				status = episode.status || 'draft';
			}
		} catch (error) {
			console.error('加载 Episode 失败:', error);
			toast.error('加载 Episode 失败');
			goto('/episodes');
		}
	};

	const handleSave = async () => {
		try {
			await updateEpisode(localStorage.token, episode.id, {
				title,
				question,
				reasoning,
				solution,
				references: references.split('\n').filter((r) => r.trim()),
				status
			});
			toast.success('保存成功');
			isEditing = false;
			await loadEpisode();
		} catch (error) {
			console.error('保存 Episode 失败:', error);
			toast.error('保存失败');
		}
	};

	const handleDelete = async () => {
		if (!confirm('确定要删除这个 Episode 吗？')) return;

		try {
			await deleteEpisode(localStorage.token, episode.id);
			toast.success('删除成功');
			goto('/episodes');
		} catch (error) {
			console.error('删除 Episode 失败:', error);
			toast.error('删除失败');
		}
	};

	const handlePublish = async () => {
		status = 'published';
		await handleSave();
	};

	onMount(async () => {
		if ($user) {
			await loadEpisode();
			loaded = true;
		}
	});
</script>

<svelte:head>
	<title>{episode?.title || '经验详情'} | 工程师助手</title>
</svelte:head>

<div class="min-h-screen max-w-[100vw] w-full">
	{#if loaded && episode}
		<div class="flex flex-col h-full">
			<!-- 头部 -->
			<div class="flex items-center justify-between px-6 py-4 border-b dark:border-gray-800">
				<div class="flex items-center gap-4">
					<button
						class="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
						on:click={() => goto('/episodes')}
					>
						← 返回
					</button>
					<div>
						<h1 class="text-xl font-semibold">{episode.title || '无标题经验'}</h1>
						<div class="flex items-center gap-2 text-sm text-gray-500">
							{#if episode.user}
								<span>{episode.user.name}</span>
							{/if}
							{#if episode.department}
								<span>· {episode.department}</span>
							{/if}
							<span>· {new Date(episode.updated_at * 1000).toLocaleString()}</span>
						</div>
					</div>
				</div>
				<div class="flex gap-2">
					{#if !isEditing}
						<button
							class="px-4 py-2 border dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800"
							on:click={() => (isEditing = true)}
						>
							编辑
						</button>
						<button
							class="px-4 py-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"
							on:click={handleDelete}
						>
							删除
						</button>
					{:else}
						<button
							class="px-4 py-2 border dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800"
							on:click={() => {
								isEditing = false;
								loadEpisode();
							}}
						>
							取消
						</button>
						{#if status === 'draft'}
							<button
								class="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
								on:click={handlePublish}
							>
								发布
							</button>
						{/if}
						<button
							class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
							on:click={handleSave}
						>
							保存
						</button>
					{/if}
				</div>
			</div>

			<!-- 内容 -->
			<div class="flex-1 overflow-y-auto px-6 py-6">
				<div class="max-w-4xl mx-auto space-y-6">
					{#if isEditing}
						<!-- 编辑模式 -->
						<div class="space-y-4">
							<div>
								<label class="block text-sm font-medium mb-1">标题</label>
								<input
									type="text"
									bind:value={title}
									class="w-full px-4 py-2 border dark:border-gray-700 rounded-lg bg-transparent"
									placeholder="输入标题（可选）"
								/>
							</div>

							<div>
								<label class="block text-sm font-medium mb-1">问题 <span class="text-red-500">*</span></label>
								<textarea
									bind:value={question}
									class="w-full px-4 py-2 border dark:border-gray-700 rounded-lg bg-transparent min-h-[100px]"
									placeholder="描述遇到的问题"
								/>
							</div>

							<div>
								<label class="block text-sm font-medium mb-1">推理过程</label>
								<textarea
									bind:value={reasoning}
									class="w-full px-4 py-2 border dark:border-gray-700 rounded-lg bg-transparent min-h-[150px]"
									placeholder="分析过程和关键步骤"
								/>
							</div>

							<div>
								<label class="block text-sm font-medium mb-1">解决方案 <span class="text-red-500">*</span></label>
								<textarea
									bind:value={solution}
									class="w-full px-4 py-2 border dark:border-gray-700 rounded-lg bg-transparent min-h-[150px]"
									placeholder="具体的解决方案"
								/>
							</div>

							<div>
								<label class="block text-sm font-medium mb-1">参考来源（每行一个）</label>
								<textarea
									bind:value={references}
									class="w-full px-4 py-2 border dark:border-gray-700 rounded-lg bg-transparent min-h-[80px]"
									placeholder="引用的文档或资料"
								/>
							</div>
						</div>
					{:else}
						<!-- 查看模式 -->
						<div class="space-y-6">
							<div>
								<h2 class="text-lg font-medium mb-2 flex items-center gap-2">
									<span class="text-blue-500">❓</span> 问题
								</h2>
								<div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
									{episode.question || '无问题描述'}
								</div>
							</div>

							{#if episode.reasoning}
								<div>
									<h2 class="text-lg font-medium mb-2 flex items-center gap-2">
										<span class="text-yellow-500">💭</span> 推理过程
									</h2>
									<div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 whitespace-pre-wrap">
										{episode.reasoning}
									</div>
								</div>
							{/if}

							<div>
								<h2 class="text-lg font-medium mb-2 flex items-center gap-2">
									<span class="text-green-500">✅</span> 解决方案
								</h2>
								<div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 whitespace-pre-wrap">
									{episode.solution || '无解决方案'}
								</div>
							</div>

							{#if episode.references && episode.references.length > 0}
								<div>
									<h2 class="text-lg font-medium mb-2 flex items-center gap-2">
										<span class="text-purple-500">📖</span> 参考来源
									</h2>
									<ul class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 space-y-1">
										{#each episode.references as ref}
											<li class="text-sm text-gray-600 dark:text-gray-400">• {ref}</li>
										{/each}
									</ul>
								</div>
							{/if}

							{#if episode.chat_id}
								<div class="pt-4 border-t dark:border-gray-700">
									<button
										class="text-sm text-blue-500 hover:text-blue-600"
										on:click={() => goto(`/c/${episode.chat_id}`)}
									>
										查看来源对话 →
									</button>
								</div>
							{/if}
						</div>
					{/if}
				</div>
			</div>
		</div>
	{:else}
		<div class="flex items-center justify-center h-full">
			<div class="text-gray-500">加载中...</div>
		</div>
	{/if}
</div>
