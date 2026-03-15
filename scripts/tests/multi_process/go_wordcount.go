package main

import (
	"encoding/csv"
	"flag"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"runtime"
	"sort"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

type WordCount map[string]int64

func main() {
	inputDir := flag.String("input", "results/preprocessed", "输入目录")
	outputFile := flag.String("output", "results/wordcount_go/wordfreq_go.csv", "输出文件")
	workers := flag.Int("workers", 8, "并发数")
	flag.Parse()

	start := time.Now()

	fmt.Println(strings.Repeat("=", 60))
	fmt.Println("Go 多线程 WordCount")
	fmt.Println(strings.Repeat("=", 60))
	fmt.Printf("输入目录: %s\n", *inputDir)
	fmt.Printf("输出文件: %s\n", *outputFile)
	fmt.Printf("并发数: %d\n", *workers)

	runtime.GOMAXPROCS(*workers)

	chunkFiles, err := filepath.Glob(filepath.Join(*inputDir, "poems_chunk_*.csv"))
	if err != nil {
		log.Fatal(err)
	}
	fmt.Printf("找到 %d 个 chunk 文件\n", len(chunkFiles))

	if len(chunkFiles) == 0 {
		log.Fatal("未找到文件")
	}

	jobs := make(chan string, len(chunkFiles))
	results := make(chan WordCount, len(chunkFiles))

	var wg sync.WaitGroup

	for i := 0; i < *workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for file := range jobs {
				count := processFile(file)
				results <- count
			}
		}()
	}

	go func() {
		for _, file := range chunkFiles {
			jobs <- file
		}
		close(jobs)
	}()

	go func() {
		wg.Wait()
		close(results)
	}()

	merged := make(WordCount)
	var totalWords int64

	for result := range results {
		for word, count := range result {
			merged[word] += count
			atomic.AddInt64(&totalWords, count)
		}
	}

	fmt.Printf("\n统计完成! 总词数: %d\n", totalWords)
	fmt.Printf("不同词数: %d\n", len(merged))

	keys := make([]string, 0, len(merged))
	for word := range merged {
		keys = append(keys, word)
	}
	sort.Slice(keys, func(i, j int) bool {
		return merged[keys[i]] > merged[keys[j]]
	})

	os.MkdirAll(filepath.Dir(*outputFile), 0755)
	out, err := os.Create(*outputFile)
	if err != nil {
		log.Fatal(err)
	}
	defer out.Close()

	writer := csv.NewWriter(out)
	writer.Write([]string{"word", "count", "rank"})

	for rank, word := range keys {
		writer.Write([]string{word, strconv.FormatInt(merged[word], 10), strconv.Itoa(rank + 1)})
	}
	writer.Flush()

	elapsed := time.Since(start)
	fmt.Printf("\n完成! 耗时: %v\n", elapsed)
	fmt.Printf("输出: %s\n", *outputFile)
}

func processFile(filepath string) WordCount {
	count := make(WordCount)

	file, err := os.Open(filepath)
	if err != nil {
		log.Printf("无法打开文件 %s: %v", filepath, err)
		return count
	}
	defer file.Close()

	reader := csv.NewReader(file)
	reader.FieldsPerRecord = -1

	_, err = reader.Read()
	if err != nil {
		log.Printf("无法读取header %s: %v", filepath, err)
		return count
	}

	for {
		record, err := reader.Read()
		if err != nil {
			break
		}

		if len(record) >= 10 {
			wordsField := record[9]
			words := strings.Fields(wordsField)
			for _, word := range words {
				if len(word) > 0 {
					count[word]++
				}
			}
		}
	}

	return count
}
