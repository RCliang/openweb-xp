<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';

	import { user } from '$lib/stores';
	import { getEpisodes, deleteEpisode } from '$lib/apis/episodes';

	let loaded = false;
	let episodes = [];
	let total = 0;
	let page = 1;
	let limit = 30;

	const loadEpisodes = async () => {
		try {
			const res = await getEpisodes(localStorage.token, (page - 1) * limit, limit);
			episodes = res.items || [];
			total = res.total || 0;
		} catch (error) {
			console.error('加载 Episode 失败:', error);
			toast.error('加载 Episode 失败');
		}
	};

	const handleDelete = async (id: string) => {
		if (!confirm('确定要删除这个 Episode 吗？')) return;

		try {
			await deleteEpisode(localStorage.token, id);
			toast.success('删除成功');
			await loadEpisodes();
		} catch (error) {
			console.error('删除 Episode 失败:', error);
			toast.error('删除失败');
		}
	};

	onMount(async () => {
		if ($user) {
			await loadEpisodes();
			loaded = true;
		}
	});
</script>

<svelte:head>
	<title>经验管理 | 工程师助手</title>
</svelte:head>

<div class="min-h-screen max-w-[100vw] w-full">
	{#if loaded}
		<div class="flex flex-col h-full">
			<!-- 头部 -->
			<div class="flex items-center justify-between px-6 py-4 border-b dark:border-gray-800">
				<div>
					<h1 class="text-2xl font-semibold">经验管理 (Episodes)</h1>
					<p class="text-gray-500 dark:text-gray-400 text-sm mt-1">
						从对话中提取的结构化经验，支持团队知识沉淀与复用
					</p>
				</div>
				<div class="flex gap-2">
					<button
						class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition"
						on:click={() => goto('/workspace')}
					>
						返回工作区
					</button>
				</div>
			</div>

			<!-- 列表 -->
			<div class="flex-1 overflow-y-auto px-6 py-4">
				{#if episodes.length === 0}
					<div class="flex flex-col items-center justify-center h-full text-gray-500">
						<div class="text-4xl mb-4">📚</div>
						<div class="text-lg">暂无经验记录</div>
						<div class="text-sm mt-2">在对话结束后，点击「保存为经验」创建新的 Episode</div>
					</div>
				{:else}
					<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
						{#each episodes as episode (episode.id)}
							<div
								class="bg-white dark:bg-gray-850 rounded-xl border dark:border-gray-800 p-4 hover:shadow-lg transition cursor-pointer"
								on:click={() => goto(`/episodes/${episode.id}`)}
							>
								<div class="flex items-start justify-between mb-2">
									<div class="flex-1">
										{#if episode.title}
											<h3 class="font-medium text-lg line-clamp-1">{episode.title}</h3>
										{:else}
											<h3 class="font-medium text-lg text-gray-400">无标题</h3>
										{/if}
										{#if episode.user}
											<span class="text-xs text-gray-500">
												{episode.user.name}
												{#if episode.department}· {episode.department}{/if}
											</span>
										{/if}
									</div>
									<span
										class="px-2 py-0.5 text-xs rounded-full {episode.status === 'published'
											? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
											: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300'}"
									>
										{episode.status === 'published' ? '已发布' : '草稿'}
									</span>
								</div>

								<p class="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 mb-3">
									{episode.question}
								</p>

								<div class="flex items-center justify-between text-xs text-gray-400">
									<span>{new Date(episode.updated_at * 1000).toLocaleDateString()}</span>
									<button
										class="text-red-500 hover:text-red-600"
										on:click|stopPropagation={() => handleDelete(episode.id)}
									>
										删除
									</button>
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		</div>
	{:else}
		<div class="flex items-center justify-center h-full">
			<div class="text-gray-500">加载中...</div>
		</div>
	{/if}
</div>
